"""Routes du module Urgences."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('urgences', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.urgences import PlanUrgenceSchema, ExerciceEvacuationSchema, MainCouranteSchema
from app.models import PlanUrgence, ExerciceEvacuation, MainCourante


@blueprint.route('/')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
def index():
    return render_template('urgences/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
@blueprint.response(200, PlanUrgenceSchema(many=True))
def api_liste():
    """Liste des plans d'urgence"""
    return PlanUrgence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(PlanUrgence.nom).all()


@blueprint.get('/api/stats')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
def api_stats():
    """Statistiques urgences"""
    eid = current_user.entreprise_id
    return {
        'plans': PlanUrgence.query.filter_by(entreprise_id=eid).count(),
        'exercices': ExerciceEvacuation.query.filter_by(entreprise_id=eid).count(),
        'incidents_ouverts': MainCourante.query.filter_by(entreprise_id=eid, statut='ouvert').count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
@blueprint.arguments(PlanUrgenceSchema)
@blueprint.response(201, PlanUrgenceSchema)
def api_creer(data):
    """Créer un nouveau plan d'urgence"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
@blueprint.arguments(PlanUrgenceSchema(partial=True))
@blueprint.response(200, PlanUrgenceSchema)
def api_modifier(data, item_id):
    """Mettre à jour un plan d'urgence"""
    item = PlanUrgence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
def api_supprimer(item_id):
    """Supprimer un plan d'urgence"""
    item = PlanUrgence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
