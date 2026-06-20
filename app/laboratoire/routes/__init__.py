"""Routes du module Laboratoire."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('laboratoire', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.laboratoire import PlanAnalyseSchema, EchantillonSchema, ResultatAnalyseSchema
from app.models import PlanAnalyse, Echantillon, ResultatAnalyse


@blueprint.route('/')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
def index():
    return render_template('laboratoire/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
@blueprint.response(200, PlanAnalyseSchema(many=True))
def api_liste():
    """Liste des plans d'analyses"""
    return PlanAnalyse.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(PlanAnalyse.nom).all()


@blueprint.get('/api/stats')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
def api_stats():
    """Statistiques laboratoire"""
    eid = current_user.entreprise_id
    return {
        'plans': PlanAnalyse.query.filter_by(entreprise_id=eid).count(),
        'echantillons': Echantillon.query.filter_by(entreprise_id=eid).count(),
        'resultats': ResultatAnalyse.query.filter_by(entreprise_id=eid).count(),
        'non_conformes': ResultatAnalyse.query.filter_by(entreprise_id=eid, conforme=False).count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
@blueprint.arguments(PlanAnalyseSchema)
@blueprint.response(201, PlanAnalyseSchema)
def api_creer(data):
    """Créer un nouveau plan d'analyse"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
@blueprint.arguments(PlanAnalyseSchema(partial=True))
@blueprint.response(200, PlanAnalyseSchema)
def api_modifier(data, item_id):
    """Mettre à jour un plan d'analyse"""
    item = PlanAnalyse.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
def api_supprimer(item_id):
    """Supprimer un plan d'analyse"""
    item = PlanAnalyse.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
