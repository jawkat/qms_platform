"""Routes du module RH QHSE."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db

import os
blueprint = Blueprint('rh_qhse', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.rh_qhse import EmployeQHSESchema
from app.models import EmployeQHSE
from datetime import date


class EmployeResource(BaseResource):
    model = EmployeQHSE
    schema = EmployeQHSESchema
    search_fields = ['matricule', 'poste', 'department']


auto_register_crud(blueprint, EmployeQHSE, EmployeQHSESchema,
                   module='rh_qhse', flat=True)


@blueprint.route('/')
@access_required(module='rh_qhse', permission='rh.voir')
def index():
    return render_template('rh_qhse/index.html')


@blueprint.get('/api/stats')
@access_required(module='rh_qhse', permission='rh.voir')
def api_stats():
    """Statistiques RH QHSE"""
    base = EmployeQHSE.query
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'visites_a_faire': base.filter(EmployeQHSE.date_prochaine_visite <= date.today()).count(),
    }
