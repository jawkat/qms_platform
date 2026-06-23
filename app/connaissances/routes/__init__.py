"""Routes du module Connaissances."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db

import os
blueprint = Blueprint('connaissances', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.connaissances import REXSchema, FAQSchema
from app.models import REX, FAQ


class REXResource(BaseResource):
    model = REX
    schema = REXSchema
    search_fields = ['titre', 'description']


@blueprint.route('/')
@access_required(module='connaissances', permission='connaissances.voir')
def index():
    return render_template('connaissances/index.html')


@blueprint.get('/api/liste')
@access_required(module='connaissances', permission='connaissances.voir')
@blueprint.response(200, REXSchema(many=True))
def api_liste():
    """Liste des retours d'expérience (REX)"""
    return REXResource.list_resources()


@blueprint.get('/api/stats')
@access_required(module='connaissances', permission='connaissances.voir')
def api_stats():
    """Statistiques de la base de connaissances"""
    return {
        'rex_total': REX.query.count(),
        'rex_publies': REX.query.filter_by(statut='publie').count(),
        'faq': FAQ.query.count(),
    }


@blueprint.post('/api/creer')
@access_required(module='connaissances', permission='connaissances.gerer')
@blueprint.arguments(REXSchema)
@blueprint.response(201, REXSchema)
def api_creer(data):
    """Créer un nouveau REX"""
    return REXResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='connaissances', permission='connaissances.gerer')
@blueprint.arguments(REXSchema(partial=True))
@blueprint.response(200, REXSchema)
def api_modifier(data, item_id):
    """Mettre à jour un REX"""
    return REXResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='connaissances', permission='connaissances.gerer')
def api_supprimer(item_id):
    """Supprimer un REX"""
    return REXResource.delete_resource(item_id)
