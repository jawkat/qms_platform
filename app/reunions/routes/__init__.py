"""Routes du module Réunions."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('reunions', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.reunions import ReunionSchema
from app.models import Reunion, ActionReunion
from datetime import datetime


class ReunionResource(BaseResource):
    model = Reunion
    schema = ReunionSchema
    search_fields = ['titre', 'lieu']


auto_register_crud(blueprint, Reunion, ReunionSchema,
                   module='reunions', flat=True)


@blueprint.route('/')
@access_required(module='reunions', permission='reunions.voir')
def index():
    return render_template('reunions/index.html')


@blueprint.get('/api/stats')
@access_required(module='reunions', permission='reunions.voir')
def api_stats():
    """Statistiques des réunions"""
    return {
        'total': Reunion.query.count(),
        'a_venir': Reunion.query.filter(Reunion.date_reunion >= datetime.utcnow()).count(),
        'actions_ouvertes': ActionReunion.query.filter_by(statut='a_faire').count(),
    }
