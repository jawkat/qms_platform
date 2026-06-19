from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.admin import admin
from app import db, mail
from app.models import (
    Utilisateur, JournalSecurite, Notification,
    SubscriptionPlan
)
from app.services.backup_service import BackupService
from app.utils.permission_catalog import iter_permission_rows, PERMISSION_CATALOG
from app.utils.subscriptions import _seed_default_plans
from functools import wraps
from flask_mail import Message


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.role or not current_user.role.est_systeme:
            abort(403)
        return f(*args, **kwargs)
    return decorated


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
