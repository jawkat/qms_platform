from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.hse import blueprint
from app.models.hse import Incident, CauseIncident
from app.schemas.hse import CauseIncidentSchema
from datetime import datetime


class CauseIncidentResource(BaseResource):
    model = CauseIncident
    schema = CauseIncidentSchema


# --- Page ---

@blueprint.route('/incidents/<int:incident_id>/causes')
@access_required(module='hse', permission='hse.voir_incidents')
def arbre_causes(incident_id):
    incident = Incident.query.filter_by(id=incident_id).first_or_404()
    return render_template('hse/causes.html', incident=incident)


# --- API: Causes d'un incident ---

@blueprint.get('/api/incidents/<int:incident_id>/causes')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.response(200, CauseIncidentSchema(many=True))
def api_causes(incident_id):
    """Liste des causes d'un incident (arbre des causes)"""
    return CauseIncident.query.filter_by(
        incident_id=incident_id,
        parent_id=None
    ).order_by(CauseIncident.ordre).all()


@blueprint.post('/api/incidents/<int:incident_id>/causes/create')
@access_required(module='hse', permission='hse.gerer_incidents')
@blueprint.arguments(CauseIncidentSchema)
@blueprint.response(201, CauseIncidentSchema)
def api_causes_create(data, incident_id):
    """Ajouter une cause à un incident"""
    data.entreprise_id = current_user.entreprise_id
    data.incident_id = incident_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/causes/<int:item_id>/update')
@access_required(module='hse', permission='hse.gerer_incidents')
@blueprint.arguments(CauseIncidentSchema(partial=True))
@blueprint.response(200, CauseIncidentSchema)
def api_causes_update(data, item_id):
    """Mettre à jour une cause"""
    return CauseIncidentResource.update_resource(item_id)


@blueprint.post('/api/causes/<int:item_id>/delete')
@access_required(module='hse', permission='hse.gerer_incidents')
def api_causes_delete(item_id):
    """Supprimer une cause"""
    return CauseIncidentResource.delete_resource(item_id)
