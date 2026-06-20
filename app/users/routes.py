from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Utilisateur, Role, Permission
from app.users import users
from app.utils.permissions import has_permission
from app.services.quota_middleware import check_quota
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


@users.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Utilisateur.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.actif:
            login_user(user)
            user.dernier_acces = __import__('datetime').datetime.utcnow()
            db.session.commit()
            return redirect(url_for('main.tableau_de_bord'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('users/login.html')


@users.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        entreprise_nom = request.form.get('entreprise', '').strip()
        pays = request.form.get('pays', 'Maroc').strip()
        taille = request.form.get('taille', 'PME').strip()
        telephone = request.form.get('telephone', '').strip()

        errors = []
        if not email:
            errors.append('Email requis.')
        elif Utilisateur.query.filter_by(email=email).first():
            errors.append('Cet email est deja utilise.')
        if not password or len(password) < 8:
            errors.append('Mot de passe minimum 8 caracteres.')
        elif password != confirm:
            errors.append('Les mots de passe ne correspondent pas.')
        if not nom:
            errors.append('Nom requis.')
        if not prenom:
            errors.append('Prenom requis.')
        if not entreprise_nom:
            errors.append("Nom d'entreprise requis.")

        if not errors:
            entreprise = Entreprise(
                nom=entreprise_nom,
                pays=pays,
                taille=taille,
                telephone=telephone or None,
                modules_actifs=['hse', 'qualite'],
                statut='Actif',
                abonnement_type='free',
                periode_essai_jours=14,
                date_debut_essai=__import__('datetime').datetime.utcnow(),
                date_inscription=__import__('datetime').date.today(),
            )
            db.session.add(entreprise)
            db.session.flush()

            role = Role.query.filter_by(nom='Manager', est_systeme=False).first()
            if not role:
                role = Role.query.filter_by(est_systeme=True).first()

            user = Utilisateur(
                nom=nom, prenom=prenom, email=email,
                actif=True, role_id=role.id if role else None,
                entreprise_id=entreprise.id, telephone=telephone or None,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            log_business_event(
                __import__('flask').current_app.logger,
                'user_registered',
                tenant_id=entreprise.id,
                user_id=user.id,
                email=email,
                entreprise=entreprise_nom,
            )

            login_user(user)
            flash('Compte cree avec succes. Bienvenue !', 'success')
            return redirect(url_for('main.tableau_de_bord'))

        for e in errors:
            flash(e, 'danger')

    return render_template('users/register.html')


@users.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.login'))


@users.route('/')
@login_required
@has_permission('users.voir')
def list_users():
    users_list = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    return render_template('users/list.html', users=users_list)


@users.route('/create', methods=['GET', 'POST'])
@login_required
@has_permission('users.cree')
@check_quota('users')
def create():
    if request.method == 'POST':
        user = Utilisateur(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=request.form['email'],
            actif=True,
            role_id=request.form.get('role_id', type=int),
            entreprise_id=current_user.entreprise_id,
        )
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        db.session.add(user)
        db.session.commit()

        from app.utils.notifications import send_account_created_email
        role_name = user.role.nom if user.role else None
        login_link = current_app.config.get('APP_LOGIN_URL', 'http://localhost:5005/')
        send_account_created_email(
            recipient_email=user.email,
            recipient_name=f"{user.prenom} {user.nom}",
            role_name=role_name,
            login_link=login_link,
        )

        flash(f'Utilisateur cree. Mot de passe temporaire: {temp_password}', 'success')
        return redirect(url_for('users.list_users'))
    roles = Role.query.filter_by(est_systeme=False).all()
    return render_template('users/create.html', roles=roles)


@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.nom = request.form['nom']
        current_user.prenom = request.form['prenom']
        db.session.commit()
        flash('Profil mis à jour.', 'success')
        return redirect(url_for('users.profile'))
    return render_template('users/profile.html')


@users.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('Mot de passe actuel incorrect.', 'danger')
        elif not new_password or len(new_password) < 8:
            flash('Le nouveau mot de passe doit contenir au moins 8 caractères.', 'danger')
        elif new_password != confirm:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Mot de passe modifié avec succès.', 'success')
            return redirect(url_for('users.profile'))
    return render_template('users/change_password.html')


@users.route('/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@has_permission('users.modifier')
def toggle_status(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    if user.entreprise_id != current_user.entreprise_id:
        flash('Utilisateur introuvable.', 'danger')
        return redirect(url_for('users.list_users'))
    user.actif = not user.actif
    db.session.commit()
    flash(f"Utilisateur {'activé' if user.actif else 'désactivé'} avec succès.", 'success')
    return redirect(url_for('users.list_users'))


@users.route('/<int:user_id>/reset-password', methods=['POST'])
@login_required
@has_permission('users.modifier')
def reset_password(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    if user.entreprise_id != current_user.entreprise_id:
        flash('Utilisateur introuvable.', 'danger')
        return redirect(url_for('users.list_users'))
    temp_password = secrets.token_urlsafe(12)
    user.set_password(temp_password)
    db.session.commit()
    flash(f"Mot de passe réinitialisé. Nouveau mot de passe temporaire: {temp_password}", 'success')
    return redirect(url_for('users.list_users'))


@users.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = Utilisateur.query.filter_by(email=email).first()
        if user:
            from app.utils.notifications import send_password_reset_email
            send_password_reset_email(user)
        flash('Si cet email existe, un lien de reinitialisation a ete envoye.', 'info')
        return redirect(url_for('users.forgot_password'))
    return render_template('users/forgot_password.html')


@users.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    user = Utilisateur.verify_reset_token(token)
    if not user:
        flash('Lien invalide ou expiré.', 'danger')
        return redirect(url_for('users.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not password or len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'danger')
        elif password != confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Mot de passe réinitialisé avec succès. Connectez-vous.', 'success')
            return redirect(url_for('users.login'))
    return render_template('users/reset_password.html')
