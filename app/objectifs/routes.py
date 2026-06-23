from flask import render_template, request, jsonify
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.objectifs import blueprint
from app.models.qualite import ObjectifQualite
from datetime import datetime


from app.schemas.objectifs import ObjectifQualiteSchema


class ObjectifResource(BaseResource):
    model = ObjectifQualite
    schema = ObjectifQualiteSchema
    search_fields = ['titre', 'description']


@blueprint.route('/')
@access_required(permission='indicateurs.voir')
def index():
    return render_template('objectifs/index.html')


@blueprint.get('/api/liste')
@access_required(permission='indicateurs.voir')
@blueprint.response(200, ObjectifQualiteSchema(many=True))
def api_liste():
    """Liste des objectifs qualité"""
    return ObjectifResource.list_resources()


@blueprint.post('/api/creer')
@access_required(permission='indicateurs.cree')
@blueprint.arguments(ObjectifQualiteSchema)
@blueprint.response(201, ObjectifQualiteSchema)
def api_creer(data):
    """Créer un nouvel objectif"""
    return ObjectifResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(permission='indicateurs.modifier')
@blueprint.arguments(ObjectifQualiteSchema(partial=True))
@blueprint.response(200, ObjectifQualiteSchema)
def api_modifier(data, item_id):
    """Modifier un objectif"""
    return ObjectifResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(permission='indicateurs.modifier')
def api_supprimer(item_id):
    """Supprimer un objectif"""
    return ObjectifResource.delete_resource(item_id)


@blueprint.get('/api/stats')
@access_required(permission='indicateurs.voir')
def api_stats():
    """Statistiques des objectifs"""
    base = ObjectifQualite.query
    return {
        'total': base.count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'atteint': base.filter_by(statut='atteint').count(),
        'en_retard': base.filter_by(statut='en_retard').count(),
        'non_atteint': base.filter_by(statut='non_atteint').count(),
    }
