"""Routes du module Environnement (ISO 14001)."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db
from datetime import datetime

import os
blueprint = Blueprint('environnement', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.environnement import AspectEnvironnementalSchema
from app.models import AspectEnvironnemental, SuiviEnvironnemental


@blueprint.route('/')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
def index():
    return render_template('environnement/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
@blueprint.response(200, AspectEnvironnementalSchema(many=True))
def api_liste():
    """Liste des aspects environnementaux"""
    return AspectEnvironnemental.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(AspectEnvironnemental.nom).all()


@blueprint.get('/api/stats')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
def api_stats():
    """Statistiques environnementales"""
    eid = current_user.entreprise_id
    return {
        'total_aspects': AspectEnvironnemental.query.filter_by(entreprise_id=eid).count(),
        'critiques': AspectEnvironnemental.query.filter_by(entreprise_id=eid, gravite='critique').count(),
        'suivis': SuiviEnvironnemental.query.filter_by(entreprise_id=eid).count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
@blueprint.arguments(AspectEnvironnementalSchema)
@blueprint.response(201, AspectEnvironnementalSchema)
def api_creer(data):
    """Identifier un nouvel aspect environnemental"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
@blueprint.arguments(AspectEnvironnementalSchema(partial=True))
@blueprint.response(200, AspectEnvironnementalSchema)
def api_modifier(data, item_id):
    """Mettre à jour un aspect environnemental"""
    item = AspectEnvironnemental.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
def api_supprimer(item_id):
    """Supprimer un aspect environnemental"""
    item = AspectEnvironnemental.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
