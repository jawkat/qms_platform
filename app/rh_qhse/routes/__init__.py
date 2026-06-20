"""Routes du module RH QHSE."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('rh_qhse', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.rh_qhse import EmployeQHSESchema
from app.models import EmployeQHSE
from datetime import date


@blueprint.route('/')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
def index():
    return render_template('rh_qhse/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
@blueprint.response(200, EmployeQHSESchema(many=True))
def api_liste():
    """Liste des employés QHSE"""
    return EmployeQHSE.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()


@blueprint.get('/api/stats')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
def api_stats():
    """Statistiques RH QHSE"""
    eid = current_user.entreprise_id
    base = EmployeQHSE.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'visites_a_faire': base.filter(EmployeQHSE.date_prochaine_visite <= date.today()).count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
@blueprint.arguments(EmployeQHSESchema)
@blueprint.response(201, EmployeQHSESchema)
def api_creer(data):
    """Ajouter un nouvel employé QHSE"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
@blueprint.arguments(EmployeQHSESchema(partial=True))
@blueprint.response(200, EmployeQHSESchema)
def api_modifier(data, item_id):
    """Modifier un employé QHSE"""
    item = EmployeQHSE.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
def api_supprimer(item_id):
    """Supprimer un employé QHSE"""
    item = EmployeQHSE.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
