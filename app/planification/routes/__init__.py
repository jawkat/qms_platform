"""Routes du module Planification."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('planification', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def index():
    return render_template('planification/index.html')


from app.schemas.planification import EvenementPlanificationSchema
from app.models import EvenementPlanification
from datetime import datetime, date


@blueprint.route('/')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def index():
    return render_template('planification/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('planification')
@has_permission('planification.voir')
@blueprint.response(200, EvenementPlanificationSchema(many=True))
def api_liste():
    """Liste des événements planifiés"""
    return EvenementPlanification.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(EvenementPlanification.date_debut).all()


@blueprint.get('/api/stats')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def api_stats():
    """Statistiques de planification"""
    eid = current_user.entreprise_id
    base = EvenementPlanification.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'a_venir': base.filter(EvenementPlanification.date_debut >= datetime.utcnow()).count(),
        'terminees': base.filter_by(statut='termine').count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('planification')
@has_permission('planification.gerer')
@blueprint.arguments(EvenementPlanificationSchema)
@blueprint.response(201, EvenementPlanificationSchema)
def api_creer(data):
    """Créer un nouvel événement"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('planification')
@has_permission('planification.gerer')
@blueprint.arguments(EvenementPlanificationSchema(partial=True))
@blueprint.response(200, EvenementPlanificationSchema)
def api_modifier(data, item_id):
    """Mettre à jour un événement"""
    item = EvenementPlanification.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.get('/api/calendrier')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def api_calendrier():
    """Calendrier des événements"""
    items = EvenementPlanification.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    couleurs = {
        'audit': '#3b82f6', 'formation': '#10b981', 'inspection': '#f59e0b',
        'maintenance': '#8b5cf6', 'reunion': '#06b6d4', 'echeance': '#ef4444',
    }
    return [{
        'id': i.id,
        'title': i.titre,
        'start': i.date_debut.isoformat() if i.date_debut else None,
        'end': i.date_fin.isoformat() if i.date_fin else None,
        'color': couleurs.get(i.type_evenement, '#6b7280'),
        'extendedProps': {
            'type': i.type_evenement,
            'pilote': f"{i.pilote.prenom} {i.pilote.nom}" if i.pilote else "N/A",
            'statut': i.statut,
        },
    } for i in items]


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('planification')
@has_permission('planification.gerer')
def api_supprimer(item_id):
    """Supprimer un événement"""
    item = EvenementPlanification.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
