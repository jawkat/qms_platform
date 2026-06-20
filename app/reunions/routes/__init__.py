"""Routes du module Réunions."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('reunions', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.reunions import ReunionSchema
from app.models import Reunion, ActionReunion
from datetime import datetime


@blueprint.route('/')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
def index():
    return render_template('reunions/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
@blueprint.response(200, ReunionSchema(many=True))
def api_liste():
    """Liste des réunions de l'entreprise"""
    return Reunion.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Reunion.date_reunion.desc()).all()


@blueprint.get('/api/stats')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
def api_stats():
    """Statistiques des réunions"""
    eid = current_user.entreprise_id
    return {
        'total': Reunion.query.filter_by(entreprise_id=eid).count(),
        'a_venir': Reunion.query.filter(Reunion.entreprise_id == eid, Reunion.date_reunion >= datetime.utcnow()).count(),
        'actions_ouvertes': ActionReunion.query.filter_by(entreprise_id=eid, statut='a_faire').count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
@blueprint.arguments(ReunionSchema)
@blueprint.response(201, ReunionSchema)
def api_creer(data):
    """Programmer une nouvelle réunion"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
@blueprint.arguments(ReunionSchema(partial=True))
@blueprint.response(200, ReunionSchema)
def api_modifier(data, item_id):
    """Mettre à jour une réunion"""
    item = Reunion.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
def api_supprimer(item_id):
    """Supprimer une réunion"""
    item = Reunion.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
