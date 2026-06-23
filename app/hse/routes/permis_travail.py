from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models.hse import Incident, EPI, Inspection, PermisTravail
from app.hse import blueprint
from app.schemas.hse import PermisTravailSchema
from datetime import date, datetime


class PermisTravailResource(BaseResource):
    model = PermisTravail
    schema = PermisTravailSchema


@blueprint.route('/permis-travail')
@access_required(module='hse', permission='hse.voir_incidents')
def permis_travail():
    return render_template('hse/permis_travail.html')


@blueprint.get('/api/permis-travail')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.response(200, PermisTravailSchema(many=True))
def api_permis_travail():
    """Liste des permis de travail HSE"""
    return PermisTravailResource.list_resources()


@blueprint.post('/api/permis-travail/create')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(PermisTravailSchema)
@blueprint.response(201, PermisTravailSchema)
def api_permis_travail_create(data):
    """Créer un permis de travail HSE"""
    return PermisTravailResource.create_resource(data)


@blueprint.post('/api/permis-travail/<int:item_id>/update')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(PermisTravailSchema(partial=True))
@blueprint.response(200, PermisTravailSchema)
def api_permis_travail_update(data, item_id):
    """Mettre à jour un permis de travail HSE"""
    return PermisTravailResource.update_resource(item_id)


@blueprint.post('/api/permis-travail/<int:item_id>/delete')
@access_required(module='hse', permission='hse.voir_incidents')
def api_permis_travail_delete(item_id):
    """Supprimer un permis de travail HSE"""
    return PermisTravailResource.delete_resource(item_id)


@blueprint.get('/api/stats')
@access_required(module='hse', permission='hse.voir_incidents')
def api_stats():
    """Statistiques HSE"""
    return {
        'incidents_total': Incident.query.count(),
        'incidents_ouverts': Incident.query.filter_by(statut='ouvert').count(),
        'incidents_accidents': Incident.query.filter_by(type_incident='accident').count(),
        'incidents_presqu_accidents': Incident.query.filter_by(type_incident='presqu_accident').count(),
        'epi_total': EPI.query.count(),
        'epi_perimes': EPI.query.filter_by(statut='perime').count(),
        'inspections_total': Inspection.query.count(),
        'inspections_nc': Inspection.query.filter_by(statut='NC').count(),
        'permis_total': PermisTravail.query.count(),
        'permis_en_cours': PermisTravail.query.filter_by(statut='autorise').count(),
    }
