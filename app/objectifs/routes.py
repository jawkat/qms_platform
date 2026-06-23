from flask import render_template, request, jsonify
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db
from app.objectifs import blueprint
from app.models.qualite import ObjectifQualite
from app.schemas.objectifs import ObjectifQualiteSchema
from datetime import datetime


class ObjectifResource(BaseResource):
    model = ObjectifQualite
    schema = ObjectifQualiteSchema
    search_fields = ['titre', 'description']


auto_register_crud(blueprint, ObjectifQualite, ObjectifQualiteSchema,
                   permission_voir='indicateurs.voir', permission_gerer='indicateurs.cree',
                   flat=True)


@blueprint.route('/')
@access_required(permission='indicateurs.voir')
def index():
    return render_template('objectifs/index.html')


@blueprint.get('/api/stats')
@access_required(permission='indicateurs.voir')
def api_stats():
    """Statistiques des objectifs"""
    base = ObjectifQualite.query
    return {
        'total': base.count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'atteint': base.filter_by(statut='atteint').count(),
        'en_retard': base.filter_by(statut='en_retard').count(),
        'non_atteint': base.filter_by(statut='non_atteint').count(),
    }
