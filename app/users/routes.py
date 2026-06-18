from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, csrf
from app.models import Utilisateur, Role, Permission
from app.users import users


@users.route('/login', methods=['GET', 'POST'])
@csrf.exempt
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


@users.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.login'))


@users.route('/')
@login_required
def list_users():
    users_list = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    return render_template('users/list.html', users=users_list)


@users.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        user = Utilisateur(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=request.form['email'],
            actif=True,
            role_id=request.form.get('role_id', type=int),
            entreprise_id=current_user.entreprise_id,
        )
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Utilisateur cree. Mot de passe temporaire: {temp_password}', 'success')
        return redirect(url_for('users.list_users'))
    roles = Role.query.filter_by(est_systeme=False).all()
    return render_template('users/create.html', roles=roles)
