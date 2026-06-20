"""Routes du module Connaissances."""
from flask import render_template, request, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('connaissances', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


from app.schemas.connaissances import REXSchema, FAQSchema
from app.models import REX, FAQ


@blueprint.route('/')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
def index():
    return render_template('connaissances/index.html')


@blueprint.get('/api/liste')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
@blueprint.response(200, REXSchema(many=True))
def api_liste():
    """Liste des retours d'expérience (REX)"""
    return REX.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(REX.date_creation.desc()).all()


@blueprint.get('/api/stats')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
def api_stats():
    """Statistiques de la base de connaissances"""
    eid = current_user.entreprise_id
    return {
        'rex_total': REX.query.filter_by(entreprise_id=eid).count(),
        'rex_publies': REX.query.filter_by(entreprise_id=eid, statut='publie').count(),
        'faq': FAQ.query.filter_by(entreprise_id=eid).count(),
    }


@blueprint.post('/api/creer')
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
@blueprint.arguments(REXSchema)
@blueprint.response(201, REXSchema)
def api_creer(data):
    """Créer un nouveau REX"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
@blueprint.arguments(REXSchema(partial=True))
@blueprint.response(200, REXSchema)
def api_modifier(data, item_id):
    """Mettre à jour un REX"""
    item = REX.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
def api_supprimer(item_id):
    """Supprimer un REX"""
    item = REX.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
