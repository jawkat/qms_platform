from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models.hse import Incident
from app.models.auth import Utilisateur
from app.utils.notifications import create_notification
from app.hse import blueprint
from app.schemas.hse import IncidentSchema
from datetime import date, datetime


class IncidentResource(BaseResource):
    model = Incident
    schema = IncidentSchema
    filter_fields = {'type': 'type_incident', 'statut': 'statut'}


@blueprint.route('/')
@access_required(module='hse', permission='hse.voir_incidents')
def tableau_de_bord():
    return render_template('hse/tableau_de_bord.html')


@blueprint.route('/incidents')
@access_required(module='hse', permission='hse.voir_incidents')
def incidents():
    return render_template('hse/incidents.html')


@blueprint.get('/api/incidents')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.response(200, IncidentSchema(many=True))
def api_incidents():
    """Liste des incidents HSE"""
    return IncidentResource.list_resources()


@blueprint.post('/api/incidents/create')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(IncidentSchema)
@blueprint.response(201, IncidentSchema)
def api_incidents_create(data):
    """Créer un incident HSE"""
    data = IncidentResource.create_resource(data)

    # Notifier les admins système
    from app.models.auth import Role
    role_admin = Role.query.filter_by(nom='Administrateur').first()
    if role_admin:
        admins = Utilisateur.query.filter_by(
            role_id=role_admin.id, actif=True
        ).all()
        type_label = {'accident': 'Accident', 'presqu_accident': 'Presqu\'accident', 'incident': 'Incident'}
        gravite_label = {'critique': 'Critique', 'majeur': 'Majeur', 'mineur': 'Mineur'}
        msg = f"{type_label.get(data.type_incident, 'Incident')} ({gravite_label.get(data.gravite, '')}) : {data.description[:80]} [INCIDENT:{data.id}]"
        for admin in admins:
            create_notification(admin.id, msg, type='incident', entite_id=data.id)

    return data


@blueprint.post('/api/incidents/<int:item_id>/update')
@access_required(module='hse', permission='hse.voir_incidents')
@blueprint.arguments(IncidentSchema(partial=True))
@blueprint.response(200, IncidentSchema)
def api_incidents_update(data, item_id):
    """Mettre à jour un incident HSE"""
    item = IncidentResource.update_resource(item_id)

    # Notifier les admins si changement de statut
    if 'statut' in request.get_json():
        from app.models.auth import Role
        role_admin = Role.query.filter_by(nom='Administrateur').first()
        if role_admin:
            admins = Utilisateur.query.filter_by(role_id=role_admin.id, actif=True).all()
            type_label = {'accident': 'Accident', 'presqu_accident': 'Presqu\'accident', 'incident': 'Incident'}
            msg = f"{type_label.get(item.type_incident, 'Incident')} → {item.statut} : {item.description[:80]} [INCIDENT:{item.id}]"
            for admin in admins:
                create_notification(admin.id, msg, type='incident', entite_id=item.id)

    return item


@blueprint.post('/api/incidents/<int:item_id>/delete')
@access_required(module='hse', permission='hse.voir_incidents')
def api_incidents_delete(item_id):
    """Supprimer un incident HSE"""
    return IncidentResource.delete_resource(item_id)
