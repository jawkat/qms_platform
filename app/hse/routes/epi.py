from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models.hse import EPI
from app.hse import blueprint
from app.schemas.hse import EPISchema
from datetime import datetime


class EPIResource(BaseResource):
    model = EPI
    schema = EPISchema


@blueprint.route('/epi')
@access_required(module='hse', permission='hse.voir_incidents')
def epi_liste():
    return render_template('hse/epi.html')


@blueprint.get('/api/epi')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.response(200, EPISchema(many=True))
def api_epi():
    """Liste des EPI (Équipements de Protection Individuelle)"""
    return EPIResource.list_resources()


@blueprint.post('/api/epi/create')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(EPISchema)
@blueprint.response(201, EPISchema)
def api_epi_create(data):
    """Créer un EPI"""
    return EPIResource.create_resource(data)


@blueprint.post('/api/epi/<int:item_id>/update')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(EPISchema(partial=True))
@blueprint.response(200, EPISchema)
def api_epi_update(data, item_id):
    """Mettre à jour un EPI"""
    return EPIResource.update_resource(item_id)


@blueprint.post('/api/epi/<int:item_id>/delete')
@access_required(module='hse', permission='hse.voir_incidents')
def api_epi_delete(item_id):
    """Supprimer un EPI"""
    return EPIResource.delete_resource(item_id)
