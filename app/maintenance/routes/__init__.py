"""Routes du module Maintenance."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('maintenance', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.maintenance import EquipementMaintenanceSchema, InterventionMaintenanceSchema
from app.models import EquipementMaintenance, InterventionMaintenance
from datetime import date


class EquipementResource(BaseResource):
    model = EquipementMaintenance
    schema = EquipementMaintenanceSchema
    search_fields = ['nom', 'reference']


auto_register_crud(blueprint, EquipementMaintenance, EquipementMaintenanceSchema,
                   module='maintenance', flat=True)


@blueprint.route('/')
@access_required(module='maintenance', permission='maintenance.voir')
def index():
    return render_template('maintenance/index.html')


@blueprint.get('/api/stats')
@access_required(module='maintenance', permission='maintenance.voir')
def api_stats():
    """Statistiques de maintenance"""
    base = EquipementMaintenance.query
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'en_panne': base.filter_by(statut='en_panne').count(),
        'maintenances_due': base.filter(EquipementMaintenance.date_prochaine_maintenance <= date.today()).count(),
        'interventions_en_cours': InterventionMaintenance.query.filter_by(statut='en_cours').count(),
    }
