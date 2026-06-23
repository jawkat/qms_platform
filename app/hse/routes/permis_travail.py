from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Incident, EPI, Inspection, PermisTravail
from app.hse import blueprint
from app.schemas.hse import PermisTravailSchema
from datetime import date, datetime


@blueprint.route('/permis-travail')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def permis_travail():
    return render_template('hse/permis_travail.html')


@blueprint.get('/api/permis-travail')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.response(200, PermisTravailSchema(many=True))
def api_permis_travail():
    """Liste des permis de travail HSE"""
    return PermisTravail.query\
        .order_by(PermisTravail.date_creation.desc()).all()


@blueprint.post('/api/permis-travail/create')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(PermisTravailSchema)
@blueprint.response(201, PermisTravailSchema)
def api_permis_travail_create(data):
    """Créer un permis de travail HSE"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/permis-travail/<int:item_id>/update')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(PermisTravailSchema(partial=True))
@blueprint.response(200, PermisTravailSchema)
def api_permis_travail_update(data, item_id):
    """Mettre à jour un permis de travail HSE"""
    item = PermisTravail.query.filter_by(id=item_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/permis-travail/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_permis_travail_delete(item_id):
    """Supprimer un permis de travail HSE"""
    item = PermisTravail.query.filter_by(id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.get('/api/stats')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
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
