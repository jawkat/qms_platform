from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.hse import blueprint
from app.models.hse import Incident, CauseIncident
from app.schemas.hse import CauseIncidentSchema
from datetime import datetime


# --- Page ---

@blueprint.route('/incidents/<int:incident_id>/causes')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def arbre_causes(incident_id):
    incident = Incident.query.filter_by(id=incident_id, entreprise_id=current_user.entreprise_id).first_or_404()
    return render_template('hse/causes.html', incident=incident)


# --- API: Causes d'un incident ---

@blueprint.get('/api/incidents/<int:incident_id>/causes')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.response(200, CauseIncidentSchema(many=True))
def api_causes(incident_id):
    """Liste des causes d'un incident (arbre des causes)"""
    return CauseIncident.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        incident_id=incident_id,
        parent_id=None
    ).order_by(CauseIncident.ordre).all()


@blueprint.post('/api/incidents/<int:incident_id>/causes/create')
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
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
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
@blueprint.arguments(CauseIncidentSchema(partial=True))
@blueprint.response(200, CauseIncidentSchema)
def api_causes_update(data, item_id):
    """Mettre à jour une cause"""
    item = CauseIncident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/causes/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
def api_causes_delete(item_id):
    """Supprimer une cause"""
    item = CauseIncident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
