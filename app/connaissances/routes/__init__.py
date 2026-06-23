"""Routes du module Connaissances."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('connaissances', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.connaissances import REXSchema, FAQSchema
from app.models import REX, FAQ


class REXResource(BaseResource):
    model = REX
    schema = REXSchema
    search_fields = ['titre', 'description']


auto_register_crud(blueprint, REX, REXSchema,
                   module='connaissances', flat=True)


@blueprint.route('/')
@access_required(module='connaissances', permission='connaissances.voir')
def index():
    return render_template('connaissances/index.html')


@blueprint.get('/api/stats')
@access_required(module='connaissances', permission='connaissances.voir')
def api_stats():
    """Statistiques de la base de connaissances"""
    return {
        'rex_total': REX.query.count(),
        'rex_publies': REX.query.filter_by(statut='publie').count(),
        'faq': FAQ.query.count(),
    }
