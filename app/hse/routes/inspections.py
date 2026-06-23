from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Inspection, InspectionItem
from app.hse import blueprint
from app.schemas.hse import InspectionSchema
from datetime import date, datetime


@blueprint.route('/inspections')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def inspections():
    return render_template('hse/inspections.html')


@blueprint.get('/api/inspections')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.response(200, InspectionSchema(many=True))
def api_inspections():
    """Liste des inspections HSE"""
    return Inspection.query\
        .order_by(Inspection.date_creation.desc()).all()


@blueprint.post('/api/inspections/create')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
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
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(InspectionSchema(partial=True))
@blueprint.response(200, InspectionSchema)
def api_inspections_update(data, item_id):
    """Mettre à jour une inspection HSE"""
    item = Inspection.query.filter_by(id=item_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation', 'items'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/inspections/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_inspections_delete(item_id):
    """Supprimer une inspection HSE"""
    item = Inspection.query.filter_by(id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
