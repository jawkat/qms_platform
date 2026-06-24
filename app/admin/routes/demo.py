from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.utils.permissions import access_required, system_admin_required
from app.admin import admin
from app import db, mail
from app.models import Disponibilite, CreneauDemo, Ticket, MessageTicket, Notification, Utilisateur, Role
from datetime import date, datetime, time, timedelta
from flask_mail import Message


@admin.route('/demo/creneaux')
@access_required()
@system_admin_required
def demo_creneaux():
    aujourdhui = date.today()
    fin = aujourdhui + timedelta(days=30)
    creneaux = CreneauDemo.query.filter(
        CreneauDemo.date_heure_debut >= datetime.combine(aujourdhui, time.min),
        CreneauDemo.date_heure_debut < datetime.combine(fin, time.max),
    ).order_by(CreneauDemo.date_heure_debut).all()
    return render_template('admin/demo_creneaux.html', creneaux=creneaux, aujourdhui=aujourdhui)


@admin.route('/demo/disponibilites', methods=['GET', 'POST'])
@access_required()
@system_admin_required
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
@access_required()
@system_admin_required
def demo_annuler_creneau(creneau_id):
    creneau = CreneauDemo.query.get_or_404(creneau_id)
    creneau.statut = 'annule'
    db.session.commit()
    flash('Créneau annulé.', 'success')
    return redirect(url_for('admin.demo_creneaux'))


@admin.route('/demo/creneaux/<int:creneau_id>/confirmer', methods=['POST'])
@access_required()
@system_admin_required
def demo_confirmer_creneau(creneau_id):
    creneau = CreneauDemo.query.get_or_404(creneau_id)
    creneau.statut = 'confirme'
    db.session.commit()
    flash('Créneau confirmé.', 'success')
    return redirect(url_for('admin.demo_creneaux'))


@admin.route('/demo/creneaux/<int:creneau_id>/rappel', methods=['POST'])
@access_required()
@system_admin_required
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
