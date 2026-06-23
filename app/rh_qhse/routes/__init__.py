"""Routes du module RH QHSE."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
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


@blueprint.route('/')
@access_required(module='rh_qhse', permission='rh.voir')
def index():
    return render_template('rh_qhse/index.html')


@blueprint.get('/api/liste')
@access_required(module='rh_qhse', permission='rh.voir')
@blueprint.response(200, EmployeQHSESchema(many=True))
def api_liste():
    """Liste des employés QHSE"""
    return EmployeResource.list_resources()


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


@blueprint.post('/api/creer')
@access_required(module='rh_qhse', permission='rh.gerer')
@blueprint.arguments(EmployeQHSESchema)
@blueprint.response(201, EmployeQHSESchema)
def api_creer(data):
    """Ajouter un nouvel employé QHSE"""
    return EmployeResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(module='rh_qhse', permission='rh.gerer')
@blueprint.arguments(EmployeQHSESchema(partial=True))
@blueprint.response(200, EmployeQHSESchema)
def api_modifier(data, item_id):
    """Modifier un employé QHSE"""
    return EmployeResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(module='rh_qhse', permission='rh.gerer')
def api_supprimer(item_id):
    """Supprimer un employé QHSE"""
    return EmployeResource.delete_resource(item_id)
