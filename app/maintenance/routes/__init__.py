"""Routes du module Maintenance."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('maintenance', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.maintenance import EquipementMaintenanceSchema, InterventionMaintenanceSchema
from app.models import EquipementMaintenance, InterventionMaintenance
from datetime import date


@blueprint.route('/')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
def index():
    return render_template('maintenance/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
@blueprint.response(200, EquipementMaintenanceSchema(many=True))
def api_liste():
    """Liste des équipements et machines"""
    return EquipementMaintenance.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(EquipementMaintenance.nom).all()


@blueprint.get('/api/stats')
@login_required
@module_active('maintenance')
@has_permission('maintenance.voir')
def api_stats():
    """Statistiques de maintenance"""
    eid = current_user.entreprise_id
    base = EquipementMaintenance.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'en_panne': base.filter_by(statut='en_panne').count(),
        'maintenances_due': base.filter(EquipementMaintenance.date_prochaine_maintenance <= date.today()).count(),
        'interventions_en_cours': InterventionMaintenance.query.filter_by(entreprise_id=eid, statut='en_cours').count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
@blueprint.arguments(EquipementMaintenanceSchema)
@blueprint.response(201, EquipementMaintenanceSchema)
def api_creer(data):
    """Ajouter un nouvel équipement"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
@blueprint.arguments(EquipementMaintenanceSchema(partial=True))
@blueprint.response(200, EquipementMaintenanceSchema)
def api_modifier(data, item_id):
    """Modifier un équipement"""
    item = EquipementMaintenance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('maintenance')
@has_permission('maintenance.gerer')
def api_supprimer(item_id):
    """Supprimer un équipement"""
    item = EquipementMaintenance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
