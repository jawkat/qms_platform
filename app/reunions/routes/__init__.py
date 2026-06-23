"""Routes du module Réunions."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db

import os
blueprint = Blueprint('reunions', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.reunions import ReunionSchema
from app.models import Reunion, ActionReunion
from datetime import datetime


class ReunionResource(BaseResource):
    model = Reunion
    schema = ReunionSchema
    search_fields = ['titre', 'lieu']


@blueprint.route('/')
@access_required(module='reunions', permission='reunions.voir')
def index():
    return render_template('reunions/index.html')


@blueprint.get('/api/liste')
@access_required(module='reunions', permission='reunions.voir')
@blueprint.response(200, ReunionSchema(many=True))
def api_liste():
    """Liste des réunions de l'entreprise"""
    return ReunionResource.list_resources()


@blueprint.get('/api/stats')
@access_required(module='reunions', permission='reunions.voir')
def api_stats():
    """Statistiques des réunions"""
    return {
        'total': Reunion.query.count(),
        'a_venir': Reunion.query.filter(Reunion.date_reunion >= datetime.utcnow()).count(),
        'actions_ouvertes': ActionReunion.query.filter_by(statut='a_faire').count(),
    }


@blueprint.post('/api/creer')
@access_required(module='reunions', permission='reunions.gerer')
@blueprint.arguments(ReunionSchema)
@blueprint.response(201, ReunionSchema)
def api_creer(data):
    """Programmer une nouvelle réunion"""
    return ReunionResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='reunions', permission='reunions.gerer')
@blueprint.arguments(ReunionSchema(partial=True))
@blueprint.response(200, ReunionSchema)
def api_modifier(data, item_id):
    """Mettre à jour une réunion"""
    return ReunionResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='reunions', permission='reunions.gerer')
def api_supprimer(item_id):
    """Supprimer une réunion"""
    return ReunionResource.delete_resource(item_id)
