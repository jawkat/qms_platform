from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Incident
from app.models.auth import Utilisateur
from app.utils.notifications import create_notification
from app.hse import blueprint
from app.schemas.hse import IncidentSchema
from datetime import date, datetime


@blueprint.route('/')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def tableau_de_bord():
    return render_template('hse/tableau_de_bord.html')


@blueprint.route('/incidents')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def incidents():
    return render_template('hse/incidents.html')


@blueprint.get('/api/incidents')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.response(200, IncidentSchema(many=True))
def api_incidents():
    """Liste des incidents HSE"""
    eid = current_user.entreprise_id
    q = Incident.query.filter_by(entreprise_id=eid)
    type_f = request.args.get('type')
    if type_f:
        q = q.filter_by(type_incident=type_f)
    statut = request.args.get('statut')
    if statut:
        q = q.filter_by(statut=statut)
    return q.order_by(Incident.date_creation.desc()).all()


@blueprint.post('/api/incidents/create')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(IncidentSchema)
@blueprint.response(201, IncidentSchema)
def api_incidents_create(data):
    """Créer un incident HSE"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()

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
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(IncidentSchema(partial=True))
@blueprint.response(200, IncidentSchema)
def api_incidents_update(data, item_id):
    """Mettre à jour un incident HSE"""
    item = Incident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()

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
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_incidents_delete(item_id):
    """Supprimer un incident HSE"""
    item = Incident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
