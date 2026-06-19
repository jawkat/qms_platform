from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise, HistoriquePaiement, SubscriptionPlan
from app.facturation import facturation
from datetime import date, datetime


@facturation.route('/')
@login_required
def index():
    return render_template('facturation/index.html', today=date.today().isoformat())


@facturation.route('/api/infos')
@login_required
def api_infos():
    e = db.session.get(Entreprise, current_user.entreprise_id)
    if not e:
        abort(404)
    plan = SubscriptionPlan.query.filter_by(plan_key=e.abonnement_type).first()
    return jsonify({
        'entreprise': e.nom,
        'abonnement_type': e.abonnement_type,
        'plan_label': plan.label if plan else e.abonnement_type,
        'prochaine_echeance': e.abonnement_prochaine_echeance.isoformat() if e.abonnement_prochaine_echeance else None,
        'abonnement_paye': e.abonnement_paye,
        'montant_annuel': float(e.montant_annuel_mad) if e.montant_annuel_mad else None,
        'contact_facturation': e.contact_facturation_email,
        'statut': e.statut,
        'date_inscription': e.date_inscription.isoformat() if e.date_inscription else None,
    })


@facturation.route('/api/paiements')
@login_required
def api_paiements():
    items = HistoriquePaiement.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(HistoriquePaiement.date_paiement.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_paiement': r.date_paiement.isoformat() if r.date_paiement else None,
        'montant_mad': float(r.montant_mad) if r.montant_mad else None,
        'methode_paiement': r.methode_paiement,
        'reference_externe': r.reference_externe,
        'statut_paiement': r.statut_paiement,
        'notes': r.notes,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@facturation.route('/api/paiements/create', methods=['POST'])
@login_required
def api_paiements_create():
    e = db.session.get(Entreprise, current_user.entreprise_id)
    if not e:
        abort(404)
    data = request.get_json()
    p = HistoriquePaiement(
        entreprise_id=current_user.entreprise_id,
        date_paiement=datetime.strptime(data['date_paiement'], '%Y-%m-%d').date() if data.get('date_paiement') else date.today(),
        montant_mad=data.get('montant_mad'),
        methode_paiement=data.get('methode_paiement'),
        reference_externe=data.get('reference_externe'),
        statut_paiement=data.get('statut_paiement', 'valide'),
        notes=data.get('notes'),
        enregistre_par=current_user.id,
    )
    e.montant_annuel_mad = data.get('montant_mad', e.montant_annuel_mad)
    e.contact_facturation_email = data.get('contact_facturation_email', e.contact_facturation_email)
    e.abonnement_paye = data.get('abonnement_paye', True)
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'id': p.id})


@facturation.route('/api/update', methods=['POST'])
@login_required
def api_update():
    e = db.session.get(Entreprise, current_user.entreprise_id)
    if not e:
        abort(404)
    data = request.get_json()
    for f in ('contact_facturation_email', 'notes_facturation'):
        if f in data:
            setattr(e, f, data[f])
    if 'montant_annuel_mad' in data:
        e.montant_annuel_mad = data['montant_annuel_mad']
    db.session.commit()
    return jsonify({'success': True})
