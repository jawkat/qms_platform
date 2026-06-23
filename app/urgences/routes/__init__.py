"""Routes du module Urgences."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('urgences', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.urgences import PlanUrgenceSchema, ExerciceEvacuationSchema, MainCouranteSchema
from app.models import PlanUrgence, ExerciceEvacuation, MainCourante


class PlanUrgenceResource(BaseResource):
    model = PlanUrgence
    schema = PlanUrgenceSchema
    search_fields = ['nom', 'description']


auto_register_crud(blueprint, PlanUrgence, PlanUrgenceSchema,
                   module='urgences', flat=True)


@blueprint.route('/')
@access_required(module='urgences', permission='urgences.voir')
def index():
    return render_template('urgences/index.html')


@blueprint.get('/api/stats')
@access_required(module='urgences', permission='urgences.voir')
def api_stats():
    """Statistiques urgences"""
    return {
        'plans': PlanUrgence.query.count(),
        'exercices': ExerciceEvacuation.query.count(),
        'incidents_ouverts': MainCourante.query.filter_by(statut='ouvert').count(),
    }
