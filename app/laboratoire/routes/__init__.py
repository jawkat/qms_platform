"""Routes du module Laboratoire."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
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


@blueprint.route('/')
@access_required(module='laboratoire', permission='laboratoire.voir')
def index():
    return render_template('laboratoire/index.html')


@blueprint.get('/api/liste')
@access_required(module='laboratoire', permission='laboratoire.voir')
@blueprint.response(200, PlanAnalyseSchema(many=True))
def api_liste():
    """Liste des plans d'analyses"""
    return PlanAnalyseResource.list_resources()


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


@blueprint.post('/api/creer')
@access_required(module='laboratoire', permission='laboratoire.gerer')
@blueprint.arguments(PlanAnalyseSchema)
@blueprint.response(201, PlanAnalyseSchema)
def api_creer(data):
    """Créer un nouveau plan d'analyse"""
    return PlanAnalyseResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='laboratoire', permission='laboratoire.gerer')
@blueprint.arguments(PlanAnalyseSchema(partial=True))
@blueprint.response(200, PlanAnalyseSchema)
def api_modifier(data, item_id):
    """Mettre à jour un plan d'analyse"""
    return PlanAnalyseResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='laboratoire', permission='laboratoire.gerer')
def api_supprimer(item_id):
    """Supprimer un plan d'analyse"""
    return PlanAnalyseResource.delete_resource(item_id)
