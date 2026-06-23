from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models.hse import Inspection, InspectionItem
from app.hse import blueprint
from app.schemas.hse import InspectionSchema
from datetime import date, datetime


class InspectionResource(BaseResource):
    model = Inspection
    schema = InspectionSchema
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation', 'items'})


@blueprint.route('/inspections')
@access_required(module='hse', permission='hse.voir_incidents')
def inspections():
    return render_template('hse/inspections.html')


@blueprint.get('/api/inspections')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.response(200, InspectionSchema(many=True))
def api_inspections():
    """Liste des inspections HSE"""
    return InspectionResource.list_resources()


@blueprint.post('/api/inspections/create')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(InspectionSchema)
@blueprint.response(201, InspectionSchema)
def api_inspections_create(data):
    """Créer une inspection HSE"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)

    # Calculation of anomalies
    anomalies = sum(1 for it in data.items if it.conforme is False)
    data.anomalies_detectees = anomalies
    if anomalies > 0:
        data.statut = 'NC'

    db.session.commit()
    return data


@blueprint.post('/api/inspections/<int:item_id>/update')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(InspectionSchema(partial=True))
@blueprint.response(200, InspectionSchema)
def api_inspections_update(data, item_id):
    """Mettre à jour une inspection HSE"""
    return InspectionResource.update_resource(item_id)


@blueprint.post('/api/inspections/<int:item_id>/delete')
@access_required(module='hse', permission='hse.voir_incidents')
def api_inspections_delete(item_id):
    """Supprimer une inspection HSE"""
    return InspectionResource.delete_resource(item_id)
