"""Routes du module Environnement (ISO 14001)."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from datetime import datetime

import os
blueprint = Blueprint('environnement', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.environnement import AspectEnvironnementalSchema
from app.models import AspectEnvironnemental, SuiviEnvironnemental


class AspectResource(BaseResource):
    model = AspectEnvironnemental
    schema = AspectEnvironnementalSchema
    search_fields = ['nom', 'impact']


@blueprint.route('/')
@access_required(module='environnement', permission='environnement.voir')
def index():
    return render_template('environnement/index.html')


@blueprint.get('/api/liste')
@access_required(module='environnement', permission='environnement.voir')
@blueprint.response(200, AspectEnvironnementalSchema(many=True))
def api_liste():
    """Liste des aspects environnementaux"""
    return AspectResource.list_resources()


@blueprint.get('/api/stats')
@access_required(module='environnement', permission='environnement.voir')
def api_stats():
    """Statistiques environnementales"""
    return {
        'total_aspects': AspectEnvironnemental.query.count(),
        'critiques': AspectEnvironnemental.query.filter_by(gravite='critique').count(),
        'suivis': SuiviEnvironnemental.query.count(),
    }


@blueprint.post('/api/creer')
@access_required(module='environnement', permission='environnement.gerer')
@blueprint.arguments(AspectEnvironnementalSchema)
@blueprint.response(201, AspectEnvironnementalSchema)
def api_creer(data):
    """Identifier un nouvel aspect environnemental"""
    return AspectResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='environnement', permission='environnement.gerer')
@blueprint.arguments(AspectEnvironnementalSchema(partial=True))
@blueprint.response(200, AspectEnvironnementalSchema)
def api_modifier(data, item_id):
    """Mettre à jour un aspect environnemental"""
    return AspectResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='environnement', permission='environnement.gerer')
def api_supprimer(item_id):
    """Supprimer un aspect environnemental"""
    return AspectResource.delete_resource(item_id)
