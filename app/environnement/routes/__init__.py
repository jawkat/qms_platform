"""Routes du module Environnement (ISO 14001)."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db
from datetime import datetime

import os
blueprint = Blueprint('environnement', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.environnement import AspectEnvironnementalSchema
from app.models import AspectEnvironnemental, SuiviEnvironnemental


class AspectResource(BaseResource):
    model = AspectEnvironnemental
    schema = AspectEnvironnementalSchema
    search_fields = ['nom', 'impact']


auto_register_crud(blueprint, AspectEnvironnemental, AspectEnvironnementalSchema,
                   module='environnement', flat=True)


@blueprint.route('/')
@access_required(module='environnement', permission='environnement.voir')
def index():
    return render_template('environnement/index.html')


@blueprint.get('/api/stats')
@access_required(module='environnement', permission='environnement.voir')
def api_stats():
    """Statistiques environnementales"""
    return {
        'total_aspects': AspectEnvironnemental.query.count(),
        'critiques': AspectEnvironnemental.query.filter_by(gravite='critique').count(),
        'suivis': SuiviEnvironnemental.query.count(),
    }
