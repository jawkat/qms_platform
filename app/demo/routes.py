from datetime import datetime, date, time, timedelta
import json
import secrets
from datetime import datetime, date, time, timedelta
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_mail import Message
from app import db, mail
from app.models import Disponibilite, CreneauDemo, Ticket, MessageTicket, Role, Utilisateur
from . import demo


DUREE_CRENEAU = 30
NB_JOURS_AFFICHES = 30


def _generer_creneaux_libres():
    aujourdhui = date.today()
    fin = aujourdhui + timedelta(days=NB_JOURS_AFFICHES)
    dispo_par_jour = {}
    for d in Disponibilite.query.filter_by(actif=True).all():
        dispo_par_jour.setdefault(d.jour_semaine, []).append((d.heure_debut, d.heure_fin))

    reserves = set()
    for c in CreneauDemo.query.filter(
        CreneauDemo.statut.in_(['reserve', 'confirme']),
        CreneauDemo.date_heure_debut >= datetime.combine(aujourdhui, time.min),
        CreneauDemo.date_heure_debut < datetime.combine(fin, time.max),
    ).all():
        reserves.add((c.date_heure_debut.date(), c.date_heure_debut.hour, c.date_heure_debut.minute))

    creneaux = []
    jour = aujourdhui
    while jour <= fin:
        plages = dispo_par_jour.get(jour.weekday(), [])
        for heure_debut, heure_fin in plages:
            h, m = heure_debut.hour, heure_debut.minute
            fin_h, fin_m = heure_fin.hour, heure_fin.minute
            while h < fin_h or (h == fin_h and m < fin_m):
                if 12 <= h < 14:
                    h, m = 14, 0
                    continue
                if (jour, h, m) not in reserves:
                    creneaux.append(datetime.combine(jour, time(h, m)))
                m += DUREE_CRENEAU
                if m >= 60:
                    h += 1
                    m = 0
        jour += timedelta(days=1)

    return creneaux


def _grouper_par_jour(creneaux):
    groupes = {}
    for dt in creneaux:
        groupes.setdefault(dt.date(), []).append(dt)
    return dict(sorted(groupes.items()))


def _slots_to_json(creneaux_par_jour):
    data = {}
    for jour, slots in creneaux_par_jour.items():
        data[jour.isoformat()] = [s.strftime('%H:%M') for s in slots]
    return json.dumps(data, default=str)


@demo.route('/reserver', methods=['GET', 'POST'])
def reserver():
    if request.method == 'POST':
        creneau_str = request.form.get('creneau', '').strip()
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip()
        entreprise = request.form.get('entreprise', '').strip()

        errors = []
        if not creneau_str:
            errors.append('Veuillez selectionner un creneau.')
        if not nom:
            errors.append('Veuillez saisir votre nom.')
        if not email:
            errors.append('Veuillez saisir votre email.')

        if not errors:
            try:
                date_heure = datetime.strptime(creneau_str, '%Y-%m-%dT%H:%M')
            except (ValueError, TypeError):
                errors.append('Creneau invalide.')

        if not errors:
            existe = CreneauDemo.query.filter_by(
                date_heure_debut=date_heure,
                statut='reserve',
            ).first()
            if existe:
                errors.append('Ce creneau vient d\'etre pris. Veuillez en choisir un autre.')

        if not errors:
            existe_email = CreneauDemo.query.filter(
                CreneauDemo.email_contact == email,
                CreneauDemo.date_heure_debut >= datetime.combine(date.today(), time.min),
                CreneauDemo.statut.in_(['reserve', 'confirme']),
            ).first()
            if existe_email:
                errors.append('Vous avez deja une reservation active. Annulez-la avant d\'en faire une nouvelle.')

        if not errors:
            room_id = secrets.token_hex(8)
            creneau = CreneauDemo(
                date_heure_debut=date_heure,
                duree_minutes=DUREE_CRENEAU,
                email_contact=email,
                nom_contact=nom,
                entreprise=entreprise or None,
                statut='reserve',
                lien_visio=f'https://meet.jit.si/ComplianceHSE-{room_id}',
            )
            db.session.add(creneau)
            db.session.commit()

            _envoyer_confirmations(creneau)

            flash('Votre demonstration a ete reservee. Vous allez recevoir un email de confirmation.', 'success')
            return redirect(url_for('main.index', _anchor='demander-devis'))

        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('main.index', _anchor='demander-devis'))

    return redirect(url_for('main.index', _anchor='demander-devis'))


@demo.route('/reserver/<token>/annuler')
def annuler(token):
    creneau = CreneauDemo.query.filter_by(token_annulation=token).first()
    if not creneau:
        flash('Lien d\'annulation invalide.', 'danger')
        return redirect(url_for('demo.reserver'))

    if creneau.statut == 'annule':
        flash('Ce creneau a deja ete annule.', 'warning')
        return redirect(url_for('demo.reserver'))

    creneau.statut = 'annule'
    db.session.commit()
    flash('Votre demonstration a ete annulee.', 'success')
    return redirect(url_for('demo.reserver'))


def _envoyer_confirmations(creneau):
    from flask import render_template
    annulation_url = url_for('demo.annuler', token=creneau.token_annulation, _external=True)
    admin_email = current_app.config.get('MAIL_ADMIN_EMAIL', 'jwd.katten@gmail.com')
    admin_url = url_for('admin.demo_creneaux', _external=True)

    try:
        html = render_template('emails/demo_confirmation.html', creneau=creneau, annulation_url=annulation_url)
        msg = Message(
            subject='Confirmation de votre demonstration HSE Compliance',
            recipients=[creneau.email_contact],
            html=html,
        )
        mail.send(msg)

        html_admin = render_template('emails/demo_admin_notification.html', creneau=creneau, admin_url=admin_url)
        msg_admin = Message(
            subject=f'Nouvelle reservation demo - {creneau.nom_contact}',
            recipients=[admin_email],
            html=html_admin,
        )
        mail.send(msg_admin)
    except Exception as e:
        current_app.logger.warning('Echec envoi email demo: %s', e)

    ticket = Ticket(
        reference=Ticket.generer_reference(),
        type='demo',
        sujet=f'Demo reservee - {creneau.nom_contact}',
        statut='nouveau',
        email_contact=creneau.email_contact,
        nom_contact=creneau.nom_contact,
        entreprise_id=None,
        cree_par_id=None,
    )
    db.session.add(ticket)
    db.session.flush()
    db.session.add(MessageTicket(
        ticket_id=ticket.id,
        auteur_type='contact',
        auteur_nom=creneau.nom_contact,
        contenu=(
            f"Demande de demonstration reservee en ligne\n\n"
            f"Creneau : {creneau.date_heure_debut.strftime('%d/%m/%Y a %H:%M')}\n"
            f"Email : {creneau.email_contact}\n"
            f"Entreprise : {creneau.entreprise or '(non renseigne)'}"
        ),
    ))
    creneau.ticket_id = ticket.id

    admins = Utilisateur.query.join(Role, Utilisateur.role_id == Role.id).filter(
        Role.est_systeme == True,
        Utilisateur.actif == True,
    ).all()
    for admin in admins:
        from app.utils.notifications import create_notification
        create_notification(admin.id, f"Nouvelle demande de demo - {creneau.nom_contact} ({creneau.email_contact}) [TICKET:{ticket.id}]", type='ticket')
    db.session.commit()
