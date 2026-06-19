from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import (
    Permission, Role, RolePermission, EntrepriseRole,
    Utilisateur, Entreprise, SubscriptionPlan, Secteur,
    TexteReglementaire, EntrepriseTexte,
    JournalSecurite, Notification, ActionCorrective,
    ProofMaster, Ticket, MessageTicket,
    Disponibilite, CreneauDemo
)
from app.services.backup_service import BackupService
from app.utils.permission_catalog import iter_permission_rows, PERMISSION_CATALOG, DEFAULT_ENTERPRISE_ROLE_PERMISSIONS
from app.utils.subscriptions import _seed_default_plans, DEFAULT_SUBSCRIPTION_PLANS
from functools import wraps
from datetime import date, datetime, time, timedelta
from flask_mail import Message
from app import mail


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.role or not current_user.role.est_systeme:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'entreprises': Entreprise.query.count(),
        'utilisateurs': Utilisateur.query.count(),
        'actions_en_cours': ActionCorrective.query.filter(
            ActionCorrective.statut.in_(['A_FAIRE', 'EN_COURS'])
        ).count(),
        'documents_actifs': ProofMaster.query.filter_by(statut='ACTIF').count(),
    }
    logs = JournalSecurite.query.order_by(JournalSecurite.date_action.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, logs=logs)


@admin.route('/entreprises')
@login_required
@admin_required
def entreprises():
    entreprises = Entreprise.query.order_by(Entreprise.date_inscription.desc()).all()
    data = []
    for e in entreprises:
        nb_users = Utilisateur.query.filter_by(entreprise_id=e.id).count()
        plan = SubscriptionPlan.query.filter_by(plan_key=e.abonnement_type).first()
        data.append({'entreprise': e, 'nb_users': nb_users, 'plan': plan})
    return render_template('admin/entreprises.html', data=data)


@admin.route('/entreprises/create', methods=['GET', 'POST'])
@login_required
@admin_required
def entreprise_create():
    if request.method == 'POST':
        modules = ['hse']
        if request.form.get('module_qualite'):
            modules.append('qualite')

        selected_secteur_ids = request.form.getlist('secteurs')

        entreprise = Entreprise(
            nom=request.form['nom'],
            taille=request.form.get('taille', 'PME'),
            pays=request.form.get('pays', 'Maroc'),
            adresse=request.form.get('adresse'),
            modules_actifs=modules,
            statut='Actif',
            date_inscription=date.today(),
        )
        db.session.add(entreprise)
        db.session.flush()

        if selected_secteur_ids:
            secteurs = Secteur.query.filter(Secteur.id.in_([int(s) for s in selected_secteur_ids if s])).all()
            entreprise.secteurs.extend(secteurs)

            textes_cibles = (
                TexteReglementaire.query
                .join(TexteReglementaire.secteurs)
                .filter(
                    Secteur.id.in_([int(s) for s in selected_secteur_ids if s]),
                    TexteReglementaire.version_active_id.isnot(None),
                )
                .distinct()
                .all()
            )

            auto_linked_count = 0
            for texte in textes_cibles:
                version_id = texte.version_active_id
                if not version_id:
                    continue

                already_linked = EntrepriseTexte.query.filter_by(
                    entreprise_id=entreprise.id,
                    texte_version_id=version_id,
                ).first()
                if already_linked:
                    continue

                db.session.add(
                    EntrepriseTexte(
                        entreprise_id=entreprise.id,
                        texte_version_id=version_id,
                        statut_obligation='OBLIGATOIRE',
                        motif_obligation='Reglementation sectorielle',
                        mode_evaluation='PERIMETRE_GLOBAL',
                    )
                )
                auto_linked_count += 1

            db.session.commit()
            flash(
                f'Entreprise creee avec succes. {auto_linked_count} texte(s) lie(s) automatiquement selon les secteurs.',
                'success',
            )
        else:
            db.session.commit()
            flash('Entreprise creee avec succes.', 'success')

        return redirect(url_for('admin.entreprises'))

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('admin/entreprise_create.html', secteurs=secteurs)


@admin.route('/entreprises/<int:eid>')
@login_required
@admin_required
def entreprise_detail(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    utilisateurs = Utilisateur.query.filter_by(entreprise_id=eid).all()
    plan = SubscriptionPlan.query.filter_by(plan_key=entreprise.abonnement_type).first()
    plans = SubscriptionPlan.query.all()
    return render_template('admin/entreprise_detail.html', entreprise=entreprise,
                           utilisateurs=utilisateurs, plan=plan, plans=plans)


@admin.route('/entreprises/<int:eid>/update', methods=['POST'])
@login_required
@admin_required
def entreprise_update(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    abonnement_type = request.form.get('abonnement_type')
    modules_actifs = request.form.getlist('modules_actifs')
    statut = request.form.get('statut')
    motif_suspension = request.form.get('motif_suspension', '').strip()

    if abonnement_type:
        entreprise.abonnement_type = abonnement_type
    if modules_actifs:
        entreprise.modules_actifs = modules_actifs
    if statut:
        entreprise.statut = statut
    if motif_suspension:
        entreprise.motif_suspension = motif_suspension
    else:
        entreprise.motif_suspension = None

    db.session.commit()
    flash('Entreprise mise à jour avec succès.', 'success')
    return redirect(url_for('admin.entreprise_detail', eid=eid))


@admin.route('/entreprises/<int:eid>/suspendre', methods=['POST'])
@login_required
@admin_required
def entreprise_suspendre(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    if entreprise.statut == 'Actif':
        entreprise.statut = 'Suspendu'
        entreprise.motif_suspension = request.form.get('motif', 'Suspendu par administrateur')
    else:
        entreprise.statut = 'Actif'
        entreprise.motif_suspension = None
    db.session.commit()
    flash(f'Entreprise {entreprise.nom} {"suspendue" if entreprise.statut == "Suspendu" else "réactivée"}.', 'success')
    return redirect(url_for('admin.entreprises'))


@admin.route('/roles')
@login_required
@admin_required
def roles():
    roles = Role.query.order_by(Role.nom).all()
    permissions = list(iter_permission_rows())
    rps = RolePermission.query.filter_by(entreprise_id=None).all()
    role_perms = {}
    for rp in rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm:
            role_perms.setdefault(rp.role_id, set()).add(perm.code)
    return render_template('admin/roles.html', roles=roles, permissions=permissions,
                           permission_catalog=PERMISSION_CATALOG,
                           DEFAULT_ENTERPRISE_ROLE_PERMISSIONS=DEFAULT_ENTERPRISE_ROLE_PERMISSIONS,
                           role_perms=role_perms)


@admin.route('/roles/create', methods=['POST'])
@login_required
@admin_required
def role_create():
    nom = request.form.get('nom', '').strip()
    description = request.form.get('description', '').strip()
    if not nom:
        flash('Le nom du rôle est requis.', 'danger')
        return redirect(url_for('admin.roles'))
    existing = Role.query.filter_by(nom=nom).first()
    if existing:
        flash('Un rôle avec ce nom existe déjà.', 'danger')
        return redirect(url_for('admin.roles'))
    role = Role(nom=nom, description=description, personnalisable=True, cree_par=current_user.id)
    db.session.add(role)
    db.session.flush()
    permission_codes = request.form.getlist('permissions')
    for code in permission_codes:
        perm = Permission.query.filter_by(code=code).first()
        if perm:
            rp = RolePermission(role_id=role.id, permission_id=perm.id, autorise=True)
            db.session.add(rp)
    db.session.commit()
    flash(f'Rôle "{nom}" créé avec succès.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/roles/<int:role_id>/edit')
@login_required
@admin_required
def role_edit(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    rps = RolePermission.query.filter_by(role_id=role.id, entreprise_id=None).all()
    role_perm_set = set()
    for rp in rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm:
            role_perm_set.add(perm.code)
    return render_template('admin/role_edit.html', role=role,
                           role_perm_set=role_perm_set,
                           permission_catalog=PERMISSION_CATALOG)


@admin.route('/roles/<int:role_id>/update', methods=['POST'])
@login_required
@admin_required
def role_update(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    description = request.form.get('description', '').strip()
    if description:
        role.description = description
    selected_codes = set(request.form.getlist('permissions'))
    existing_rps = RolePermission.query.filter_by(role_id=role.id, entreprise_id=None).all()
    for rp in existing_rps:
        perm = db.session.get(Permission, rp.permission_id)
        if perm and perm.code not in selected_codes:
            db.session.delete(rp)
        elif perm and perm.code in selected_codes:
            selected_codes.discard(perm.code)
    for code in selected_codes:
        perm = Permission.query.filter_by(code=code).first()
        if perm:
            rp = RolePermission(role_id=role.id, permission_id=perm.id, entreprise_id=None, autorise=True)
            db.session.add(rp)
    db.session.commit()
    flash(f'Rôle "{role.nom}" mis à jour.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@admin_required
def role_delete(role_id):
    role = db.session.get(Role, role_id)
    if not role:
        abort(404)
    if not role.personnalisable:
        flash('Ce rôle système ne peut pas être supprimé.', 'danger')
        return redirect(url_for('admin.roles'))
    if Utilisateur.query.filter_by(role_id=role.id).count() > 0:
        flash('Ce rôle est attribué à des utilisateurs.', 'danger')
        return redirect(url_for('admin.roles'))
    RolePermission.query.filter_by(role_id=role.id).delete()
    EntrepriseRole.query.filter_by(role_id=role.id).delete()
    db.session.delete(role)
    db.session.commit()
    flash(f'Rôle "{role.nom}" supprimé.', 'success')
    return redirect(url_for('admin.roles'))


@admin.route('/permissions')
@login_required
@admin_required
def permissions():
    perms = list(iter_permission_rows())
    return render_template('admin/permissions.html', permissions=perms,
                           permission_catalog=PERMISSION_CATALOG)


@admin.route('/securite')
@login_required
@admin_required
def securite():
    type_action = request.args.get('type_action')
    query = JournalSecurite.query
    if type_action:
        query = query.filter_by(type_action=type_action)
    logs = query.order_by(JournalSecurite.date_action.desc()).all()
    types = [t[0] for t in db.session.query(JournalSecurite.type_action).distinct().all()]
    utilisateurs = {u.id: u for u in Utilisateur.query.all()}
    return render_template('admin/securite.html', logs=logs, types=types, utilisateurs=utilisateurs)


@admin.route('/notifications')
@login_required
@admin_required
def notifications():
    notifs = Notification.query.order_by(Notification.date_envoi.desc()).all()
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom).all()
    users_dict = {u.id: u for u in utilisateurs}
    return render_template('admin/notifications.html', notifications=notifs,
                           utilisateurs=utilisateurs, users_dict=users_dict)


@admin.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def notification_send():
    type_notif = request.form.get('type', 'info')
    message = request.form.get('message', '').strip()
    utilisateur_id = request.form.get('utilisateur_id')
    if not message:
        flash('Le message est requis.', 'danger')
        return redirect(url_for('admin.notifications'))
    if utilisateur_id:
        notif = Notification(type=type_notif, message=message, utilisateur_id=int(utilisateur_id))
        db.session.add(notif)
    else:
        for u in Utilisateur.query.all():
            db.session.add(Notification(type=type_notif, message=message, utilisateur_id=u.id))
    db.session.commit()
    flash('Notification(s) envoyée(s).', 'success')
    return redirect(url_for('admin.notifications'))


@admin.route('/plans')
@login_required
@admin_required
def plans():
    plans_list = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    all_feature_keys = []
    seen = set()
    for p in plans_list:
        if p.features:
            for k in p.features:
                if k not in seen:
                    all_feature_keys.append(k)
                    seen.add(k)
    return render_template('admin/plans.html', plans=plans_list,
                           all_feature_keys=all_feature_keys)


@admin.route('/plans/seed', methods=['POST'])
@login_required
@admin_required
def plans_seed():
    _seed_default_plans()
    flash('Plans d\'abonnement par défaut créés.', 'success')
    return redirect(url_for('admin.plans'))


@admin.route('/backups')
@login_required
@admin_required
def backups():
    service = BackupService()
    backups_list = service.list_backups()
    return render_template('admin/backups.html', backups=backups_list)


@admin.route('/backups/create', methods=['POST'])
@login_required
@admin_required
def backup_create():
    service = BackupService()
    try:
        filename = service.create_backup()
        flash(f'Sauvegarde créée : {filename}', 'success')
    except Exception as e:
        flash(f'Erreur lors de la création de la sauvegarde : {e}', 'danger')
    return redirect(url_for('admin.backups'))


@admin.route('/backups/<filename>/restore', methods=['POST'])
@login_required
@admin_required
def backup_restore(filename):
    service = BackupService()
    try:
        service.restore_backup(filename)
        flash(f'Sauvegarde restaurée : {filename}', 'success')
    except Exception as e:
        flash(f'Erreur lors de la restauration : {e}', 'danger')
    return redirect(url_for('admin.backups'))


@admin.route('/backups/<filename>/delete', methods=['POST'])
@login_required
@admin_required
def backup_delete(filename):
    service = BackupService()
    if service.delete_backup(filename):
        flash(f'Sauvegarde supprimée : {filename}', 'success')
    else:
        flash(f'Fichier introuvable : {filename}', 'danger')
    return redirect(url_for('admin.backups'))


@admin.route('/utilisateurs')
@login_required
@admin_required
def utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.nom).all()
    return render_template('admin/utilisateurs.html', users=users)


@admin.route('/utilisateurs/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    user.actif = not user.actif
    db.session.commit()
    flash(f"Utilisateur {'activé' if user.actif else 'désactivé'}.", 'success')
    return redirect(url_for('admin.utilisateurs'))


@admin.route('/utilisateurs/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_user_password(user_id):
    import secrets as _secrets
    user = Utilisateur.query.get_or_404(user_id)
    temp = _secrets.token_urlsafe(12)
    user.set_password(temp)
    db.session.commit()
    flash(f"Mot de passe réinitialisé. Nouveau : {temp}", 'success')
    return redirect(url_for('admin.utilisateurs'))


@admin.route('/tickets')
@login_required
@admin_required
def admin_tickets():
    tickets = Ticket.query.order_by(Ticket.date_creation.desc()).all()
    return render_template('admin/tickets.html', tickets=tickets)


@admin.route('/tickets/<int:ticket_id>/fermer', methods=['POST'])
@login_required
@admin_required
def admin_ticket_fermer(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.statut = 'ferme'
    db.session.commit()
    flash('Ticket fermé.', 'success')
    return redirect(url_for('admin.admin_tickets'))


# --- Demo management ---

@admin.route('/demo/creneaux')
@login_required
@admin_required
def demo_creneaux():
    aujourdhui = date.today()
    fin = aujourdhui + timedelta(days=30)
    creneaux = CreneauDemo.query.filter(
        CreneauDemo.date_heure_debut >= datetime.combine(aujourdhui, time.min),
        CreneauDemo.date_heure_debut < datetime.combine(fin, time.max),
    ).order_by(CreneauDemo.date_heure_debut).all()
    return render_template('admin/demo_creneaux.html', creneaux=creneaux, aujourdhui=aujourdhui)


@admin.route('/demo/disponibilites', methods=['GET', 'POST'])
@login_required
@admin_required
def demo_disponibilites():
    if request.method == 'POST':
        Disponibilite.query.delete()
        jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        for i, jour in enumerate(jours):
            actif = request.form.get(f'actif_{i}') == '1'
            debut = request.form.get(f'debut_{i}')
            fin = request.form.get(f'fin_{i}')
            if actif and debut and fin:
                try:
                    h_debut, m_debut = map(int, debut.split(':'))
                    h_fin, m_fin = map(int, fin.split(':'))
                    db.session.add(Disponibilite(
                        jour_semaine=i,
                        heure_debut=time(h_debut, m_debut),
                        heure_fin=time(h_fin, m_fin),
                        actif=True,
                    ))
                except (ValueError, TypeError):
                    pass
        db.session.commit()
        flash('Disponibilités mises à jour.', 'success')
        return redirect(url_for('admin.demo_disponibilites'))

    dispo_par_jour = {d.jour_semaine: d for d in Disponibilite.query.filter_by(actif=True).all()}
    if not dispo_par_jour:
        defauts = {
            0: ('10:00', '12:00'), 1: ('10:00', '12:00'), 2: ('10:00', '12:00'),
            3: ('10:00', '12:00'), 4: ('10:00', '12:00'),
        }
        for jour, (debut, fin) in defauts.items():
            h_d, m_d = map(int, debut.split(':'))
            h_f, m_f = map(int, fin.split(':'))
            disp = Disponibilite(jour_semaine=jour, heure_debut=time(h_d, m_d), heure_fin=time(h_f, m_f), actif=True)
            db.session.add(disp)
        disp_apres_midi = {
            0: ('15:00', '16:00'), 1: ('15:00', '16:00'), 2: ('15:00', '16:00'),
            3: ('15:00', '16:00'), 4: ('15:00', '16:00'),
        }
        for jour, (debut, fin) in disp_apres_midi.items():
            h_d, m_d = map(int, debut.split(':'))
            h_f, m_f = map(int, fin.split(':'))
            disp = Disponibilite(jour_semaine=jour, heure_debut=time(h_d, m_d), heure_fin=time(h_f, m_f), actif=True)
            db.session.add(disp)
        db.session.commit()
        dispo_par_jour = {d.jour_semaine: d for d in Disponibilite.query.filter_by(actif=True).all()}
    return render_template('admin/demo_disponibilites.html', dispo_par_jour=dispo_par_jour)


@admin.route('/demo/creneaux/<int:creneau_id>/annuler', methods=['POST'])
@login_required
@admin_required
def demo_annuler_creneau(creneau_id):
    creneau = CreneauDemo.query.get_or_404(creneau_id)
    creneau.statut = 'annule'
    db.session.commit()
    flash('Créneau annulé.', 'success')
    return redirect(url_for('admin.demo_creneaux'))


@admin.route('/demo/creneaux/<int:creneau_id>/confirmer', methods=['POST'])
@login_required
@admin_required
def demo_confirmer_creneau(creneau_id):
    creneau = CreneauDemo.query.get_or_404(creneau_id)
    creneau.statut = 'confirme'
    db.session.commit()
    flash('Créneau confirmé.', 'success')
    return redirect(url_for('admin.demo_creneaux'))


@admin.route('/demo/creneaux/<int:creneau_id>/rappel', methods=['POST'])
@login_required
@admin_required
def demo_rappel_creneau(creneau_id):
    creneau = CreneauDemo.query.get_or_404(creneau_id)
    annulation_url = url_for('demo.annuler', token=creneau.token_annulation, _external=True)
    html = render_template('emails/demo_confirmation.html', creneau=creneau, annulation_url=annulation_url)
    msg = Message(
        subject='Rappel - Votre démonstration QMS Platform',
        recipients=[creneau.email_contact],
        html=html,
    )
    mail.send(msg)
    creneau.nb_rappels = (creneau.nb_rappels or 0) + 1
    db.session.commit()
    flash(f'Email de rappel envoyé à {creneau.email_contact} ({creneau.nb_rappels}x).', 'success')
    return redirect(url_for('admin.demo_creneaux'))
