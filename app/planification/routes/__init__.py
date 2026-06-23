"""Routes du module Planification."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db

import os
blueprint = Blueprint('planification', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@access_required(module='planification', permission='planification.voir')
def index():
    return render_template('planification/index.html')


from app.schemas.planification import EvenementPlanificationSchema
from app.models import EvenementPlanification
from datetime import datetime, date


@blueprint.route('/')
@access_required(module='planification', permission='planification.voir')
def index():
    return render_template('planification/index.html')


@blueprint.get('/api/liste')
@access_required(module='planification', permission='planification.voir')
@blueprint.response(200, EvenementPlanificationSchema(many=True))
def api_liste():
    """Liste des événements planifiés"""
    return EvenementResource.list_resources()


@blueprint.get('/api/stats')
@access_required(module='planification', permission='planification.voir')
def api_stats():
    """Statistiques de planification"""
    base = EvenementPlanification.query
    return {
        'total': base.count(),
        'a_venir': base.filter(EvenementPlanification.date_debut >= datetime.utcnow()).count(),
        'terminees': base.filter_by(statut='termine').count(),
    }


@blueprint.post('/api/creer')
@access_required(module='planification', permission='planification.gerer')
@blueprint.arguments(EvenementPlanificationSchema)
@blueprint.response(201, EvenementPlanificationSchema)
def api_creer(data):
    """Créer un nouvel événement"""
    return EvenementResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='planification', permission='planification.gerer')
@blueprint.arguments(EvenementPlanificationSchema(partial=True))
@blueprint.response(200, EvenementPlanificationSchema)
def api_modifier(data, item_id):
    """Mettre à jour un événement"""
    return EvenementResource.update_resource(item_id)


@blueprint.get('/api/calendrier')
@access_required(module='planification', permission='planification.voir')
def api_calendrier():
    """Calendrier des événements"""
    items = EvenementPlanification.query.all()
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
@access_required(module='planification', permission='planification.gerer')
def api_supprimer(item_id):
    """Supprimer un événement"""
    return EvenementResource.delete_resource(item_id)
