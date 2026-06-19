from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import Utilisateur, Ticket, MessageTicket
from functools import wraps
import secrets


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.role or not current_user.role.est_systeme:
            abort(403)
        return f(*args, **kwargs)
    return decorated


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
    user = Utilisateur.query.get_or_404(user_id)
    temp = secrets.token_urlsafe(12)
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
