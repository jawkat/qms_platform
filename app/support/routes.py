import secrets
from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Ticket, MessageTicket, Utilisateur, Role
from app.support import support
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import has_permission
from app.schemas.support import TicketSchema


STATUTS = ['OUVERT', 'EN_COURS', 'ATTENTE', 'FERME']
TYPES = ['technique', 'facturation', 'commercial', 'autre']


def _get_admins():
    return Utilisateur.query.join(Role, Utilisateur.role_id == Role.id) \
                            .filter(Role.est_systeme == True).all()


def _notifier_admins(ticket, message=None):
    from app.utils.notifications import create_notification
    admins = _get_admins()
    for admin in admins:
        msg = f"Nouveau ticket {ticket.reference}: {ticket.sujet}"
        if message:
            msg = f"Nouveau message sur {ticket.reference}: {message.contenu[:100]}"
        create_notification(admin.id, f"{msg} [TICKET:{ticket.id}]", type='ticket')


def _notifier_client(ticket, message):
    if ticket.cree_par_id:
        from app.utils.notifications import create_notification
        create_notification(ticket.cree_par_id, f"Nouvelle réponse sur {ticket.reference}: {message.contenu[:100]} [TICKET:{ticket.id}]", type='ticket')


@support.route('/')
@support.route('/mes-tickets')
@login_required
@has_permission('support.voir')
def mes_tickets():
    q = Ticket.query
    statut = request.args.get('statut')
    type_ = request.args.get('type')
    search = request.args.get('search')
    if statut:
        q = q.filter(Ticket.statut == statut)
    if type_:
        q = q.filter(Ticket.type == type_)
    if search:
        q = q.filter(
            db.or_(
                Ticket.sujet.ilike(f'%{search}%'),
                Ticket.reference.ilike(f'%{search}%'),
                Ticket.email_contact.ilike(f'%{search}%'))
        )
    tickets = q.order_by(Ticket.date_dernier_message.desc().nullslast(),
                         Ticket.date_creation.desc()).all()

    last_messages = {}
    for t in tickets:
        last_msg = MessageTicket.query.filter_by(ticket_id=t.id) \
            .order_by(MessageTicket.date_envoi.desc()).first()
        last_messages[t.id] = last_msg

    return render_template('support/tickets.html', tickets=tickets,
                           statuts=STATUTS, types=TYPES, filters=request.args,
                           last_messages=last_messages)


@support.route('/creer', methods=['GET', 'POST'])
@login_required
@has_permission('support.cree')
def creer_ticket():
    if request.method == 'POST':
        reference = Ticket.generer_reference()
        ticket = Ticket(
            reference=reference,
            type=request.form['type'],
            sujet=request.form['sujet'],
            statut='OUVERT',
            email_contact=request.form.get('email_contact') or None,
            nom_contact=request.form.get('nom_contact') or None,
            telephone=request.form.get('telephone') or None,
            entreprise_id=current_user.entreprise_id,
            cree_par_id=current_user.id,
            date_creation=datetime.utcnow(),
            date_dernier_message=datetime.utcnow(),
        )
        db.session.add(ticket)
        db.session.flush()
        msg = MessageTicket(
            ticket_id=ticket.id,
            auteur_type='utilisateur',
            auteur_nom=current_user.prenom + ' ' + current_user.nom,
            contenu=request.form['contenu'],
            est_interne=False,
            date_envoi=datetime.utcnow(),
        )
        db.session.add(msg)
        _notifier_admins(ticket)
        db.session.commit()
        flash('Ticket créé avec succès.', 'success')
        return redirect(url_for('support.detail_ticket', ticket_id=ticket.id))
    return render_template('support/creer_ticket.html', types=TYPES)


@support.route('/<int:ticket_id>')
@login_required
@has_permission('support.voir')
def detail_ticket(ticket_id):
    ticket = tenant_get_or_404(Ticket, ticket_id)
    messages = MessageTicket.query.filter_by(ticket_id=ticket.id) \
        .filter(MessageTicket.est_interne == False) \
        .order_by(MessageTicket.date_envoi.asc()).all()
    return render_template('support/ticket_detail.html', ticket=ticket,
                           messages=messages, statuts=STATUTS)


@support.route('/<int:ticket_id>/message', methods=['POST'])
@login_required
@has_permission('support.voir')
def ajouter_message(ticket_id):
    ticket = tenant_get_or_404(Ticket, ticket_id)
    if ticket.statut == 'FERME':
        flash('Ce ticket est fermé.', 'warning')
        return redirect(url_for('support.detail_ticket', ticket_id=ticket.id))
    contenu = request.form.get('contenu', '').strip()
    if not contenu:
        flash('Le message ne peut pas être vide.', 'danger')
        return redirect(url_for('support.detail_ticket', ticket_id=ticket.id))
    msg = MessageTicket(
        ticket_id=ticket.id,
        auteur_type='utilisateur',
        auteur_nom=current_user.prenom + ' ' + current_user.nom,
        contenu=contenu,
        est_interne=False,
        date_envoi=datetime.utcnow(),
    )
    db.session.add(msg)
    ticket.date_dernier_message = datetime.utcnow()
    if ticket.statut == 'OUVERT':
        ticket.statut = 'EN_COURS'
    _notifier_admins(ticket, msg)
    db.session.commit()
    flash('Message ajouté.', 'success')
    return redirect(url_for('support.detail_ticket', ticket_id=ticket.id))


@support.route('/<int:ticket_id>/fermer', methods=['POST'])
@login_required
@has_permission('support.fermer')
def fermer_ticket(ticket_id):
    ticket = tenant_get_or_404(Ticket, ticket_id)
    if ticket.statut != 'FERME':
        ticket.statut = 'FERME'
        ticket.date_fermeture = datetime.utcnow()
        db.session.commit()
        flash('Ticket fermé.', 'success')
    else:
        flash('Ce ticket est déjà fermé.', 'info')
    return redirect(url_for('support.detail_ticket', ticket_id=ticket.id))


@support.get('/api/liste')
@login_required
@has_permission('support.voir')
@support.response(200, TicketSchema(many=True))
def api_liste():
    """Liste de vos tickets support"""
    return Ticket.query \
        .order_by(Ticket.date_creation.desc()).all()
