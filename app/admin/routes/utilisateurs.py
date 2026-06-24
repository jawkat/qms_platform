from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.utils.permissions import access_required, system_admin_required
from app.admin import admin
from app import db
from app.models import Utilisateur, Ticket, MessageTicket
from datetime import datetime
import secrets


@admin.route('/utilisateurs')
@access_required()
@system_admin_required
def utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.nom).all()
    return render_template('admin/utilisateurs.html', users=users)


@admin.route('/utilisateurs/<int:user_id>/toggle', methods=['POST'])
@access_required()
@system_admin_required
def admin_toggle_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    user.actif = not user.actif
    db.session.commit()
    flash(f"Utilisateur {'activé' if user.actif else 'désactivé'}.", 'success')
    dest = request.form.get('redirect_url') or request.referrer or url_for('admin.utilisateurs')
    return redirect(dest)


@admin.route('/utilisateurs/<int:user_id>/reset-password', methods=['POST'])
@access_required()
@system_admin_required
def admin_reset_user_password(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    temp = secrets.token_urlsafe(12)
    user.set_password(temp)
    db.session.commit()
    flash(f"Mot de passe réinitialisé. Nouveau : {temp}", 'success')
    dest = request.form.get('redirect_url') or request.referrer or url_for('admin.utilisateurs')
    return redirect(dest)


# ─── Tickets support ────────────────────────────────────────────

@admin.route('/tickets')
@access_required()
@system_admin_required
def admin_tickets():
    type_filter = request.args.get('type', '')
    statut_filter = request.args.get('statut', '')

    query = Ticket.query.order_by(Ticket.date_dernier_message.desc().nullslast(),
                                  Ticket.date_creation.desc())
    if type_filter:
        query = query.filter(Ticket.type == type_filter)
    if statut_filter:
        query = query.filter(Ticket.statut == statut_filter)
    tickets = query.all()

    types = db.session.query(Ticket.type).distinct().all()
    types = sorted(set(t[0] for t in types if t[0]))

    last_messages = {}
    for t in tickets:
        last_msg = MessageTicket.query.filter_by(ticket_id=t.id) \
            .order_by(MessageTicket.date_envoi.desc()).first()
        last_messages[t.id] = last_msg

    return render_template('admin/tickets.html', tickets=tickets,
                           types=types, type_filter=type_filter,
                           statut_filter=statut_filter, last_messages=last_messages)


@admin.route('/tickets/<int:ticket_id>')
@access_required()
@system_admin_required
def admin_ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    messages = MessageTicket.query.filter_by(ticket_id=ticket.id) \
        .order_by(MessageTicket.date_envoi.asc()).all()
    return render_template('admin/ticket_detail.html', ticket=ticket, messages=messages)


@admin.route('/tickets/<int:ticket_id>/message', methods=['POST'])
@access_required()
@system_admin_required
def admin_ticket_repondre(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    contenu = request.form.get('contenu', '').strip()
    est_interne = request.form.get('est_interne') == '1'

    if not contenu:
        flash('Le message est vide.', 'warning')
        return redirect(url_for('admin.admin_ticket_detail', ticket_id=ticket_id))

    msg = MessageTicket(
        ticket_id=ticket.id,
        auteur_type='admin',
        auteur_nom=f"{current_user.prenom} {current_user.nom}",
        contenu=contenu,
        est_interne=est_interne,
    )
    db.session.add(msg)
    ticket.date_dernier_message = msg.date_envoi
    if ticket.statut in ('OUVERT', 'ATTENTE'):
        ticket.statut = 'EN_COURS'
    db.session.commit()

    if not est_interne and ticket.cree_par_id:
        from app.utils.notifications import create_notification
        create_notification(ticket.cree_par_id, f"Nouvelle réponse sur {ticket.reference}: {contenu[:100]} [TICKET:{ticket.id}]", type='ticket')
        db.session.commit()

    flash('Message ajouté.', 'success')
    return redirect(url_for('admin.admin_ticket_detail', ticket_id=ticket_id))


@admin.route('/tickets/<int:ticket_id>/statut', methods=['POST'])
@access_required()
@system_admin_required
def admin_ticket_changer_statut(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    nouveau_statut = request.form.get('statut', '').strip()

    if nouveau_statut in ('OUVERT', 'EN_COURS', 'ATTENTE', 'FERME'):
        ticket.statut = nouveau_statut
        if nouveau_statut == 'FERME':
            ticket.date_fermeture = datetime.utcnow()
        db.session.commit()
        flash(f"Statut changé en « {nouveau_statut} ».", 'success')
    else:
        flash('Statut invalide.', 'warning')

    return redirect(url_for('admin.admin_ticket_detail', ticket_id=ticket.id))
