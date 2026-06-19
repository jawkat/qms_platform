"""Routes du module Maintenance."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

blueprint = Blueprint('maintenance', __name__, template_folder='templates')


@blueprint.route('/')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
def index():
    return render_template('maintenance/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
def api_liste():
    from app.maintenance.models import EquipementMaintenance
    items = EquipementMaintenance.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(EquipementMaintenance.nom).all()
    return jsonify([{
        'id': i.id, 'nom': i.nom, 'reference': i.reference,
        'description': i.description, 'localisation': i.localisation,
        'categorie': i.categorie, 'statut': i.statut,
        'date_derniere_maintenance': i.date_derniere_maintenance.isoformat() if i.date_derniere_maintenance else None,
        'date_prochaine_maintenance': i.date_prochaine_maintenance.isoformat() if i.date_prochaine_maintenance else None,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
def api_stats():
    from app.maintenance.models import EquipementMaintenance, InterventionMaintenance
    from datetime import date
    eid = current_user.entreprise_id
    base = EquipementMaintenance.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'en_panne': base.filter_by(statut='en_panne').count(),
        'maintenances_due': base.filter(EquipementMaintenance.date_prochaine_maintenance <= date.today()).count() if base.filter(EquipementMaintenance.date_prochaine_maintenance.isnot(None)).count() else 0,
        'interventions_en_cours': InterventionMaintenance.query.filter_by(entreprise_id=eid, statut='en_cours').count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
def api_creer():
    from app.maintenance.models import EquipementMaintenance
    from datetime import datetime
    data = request.get_json()
    item = EquipementMaintenance(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), reference=data.get('reference'),
        description=data.get('description'), localisation=data.get('localisation'),
        categorie=data.get('categorie'), frequence_maintenance=data.get('frequence_maintenance'),
    )
    if data.get('date_acquisition'):
        item.date_acquisition = datetime.strptime(data['date_acquisition'], '%Y-%m-%d').date()
    if data.get('date_prochaine_maintenance'):
        item.date_prochaine_maintenance = datetime.strptime(data['date_prochaine_maintenance'], '%Y-%m-%d').date()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
def api_modifier(item_id):
    from app.maintenance.models import EquipementMaintenance
    from datetime import datetime
    item = EquipementMaintenance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'reference', 'description', 'localisation', 'categorie', 'frequence_maintenance', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_prochaine_maintenance'):
        item.date_prochaine_maintenance = datetime.strptime(data['date_prochaine_maintenance'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
def api_supprimer(item_id):
    from app.maintenance.models import EquipementMaintenance
    item = EquipementMaintenance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
