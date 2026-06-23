"""Routes du module Urgences."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
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


@blueprint.route('/')
@access_required(module='urgences', permission='urgences.voir')
def index():
    return render_template('urgences/index.html')


@blueprint.get('/api/liste')
@access_required(module='urgences', permission='urgences.voir')
@blueprint.response(200, PlanUrgenceSchema(many=True))
def api_liste():
    """Liste des plans d'urgence"""
    return PlanUrgenceResource.list_resources()


@blueprint.get('/api/stats')
@access_required(module='urgences', permission='urgences.voir')
def api_stats():
    """Statistiques urgences"""
    return {
        'plans': PlanUrgence.query.count(),
        'exercices': ExerciceEvacuation.query.count(),
        'incidents_ouverts': MainCourante.query.filter_by(statut='ouvert').count(),
    }


@blueprint.post('/api/creer')
@access_required(module='urgences', permission='urgences.gerer')
@blueprint.arguments(PlanUrgenceSchema)
@blueprint.response(201, PlanUrgenceSchema)
def api_creer(data):
    """Créer un nouveau plan d'urgence"""
    return PlanUrgenceResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='urgences', permission='urgences.gerer')
@blueprint.arguments(PlanUrgenceSchema(partial=True))
@blueprint.response(200, PlanUrgenceSchema)
def api_modifier(data, item_id):
    """Mettre à jour un plan d'urgence"""
    return PlanUrgenceResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='urgences', permission='urgences.gerer')
def api_supprimer(item_id):
    """Supprimer un plan d'urgence"""
    return PlanUrgenceResource.delete_resource(item_id)
