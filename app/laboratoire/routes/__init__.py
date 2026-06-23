"""Routes du module Laboratoire."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('laboratoire', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.laboratoire import PlanAnalyseSchema, EchantillonSchema, ResultatAnalyseSchema
from app.models import PlanAnalyse, Echantillon, ResultatAnalyse


class PlanAnalyseResource(BaseResource):
    model = PlanAnalyse
    schema = PlanAnalyseSchema
    search_fields = ['nom', 'produit_concerne', 'parametre']


auto_register_crud(blueprint, PlanAnalyse, PlanAnalyseSchema,
                   module='laboratoire', flat=True)


@blueprint.route('/')
@access_required(module='laboratoire', permission='laboratoire.voir')
def index():
    return render_template('laboratoire/index.html')


@blueprint.get('/api/stats')
@access_required(module='laboratoire', permission='laboratoire.voir')
def api_stats():
    """Statistiques laboratoire"""
    return {
        'plans': PlanAnalyse.query.count(),
        'echantillons': Echantillon.query.count(),
        'resultats': ResultatAnalyse.query.count(),
        'non_conformes': ResultatAnalyse.query.filter_by(conforme=False).count(),
    }
