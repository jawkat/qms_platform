"""Routes du module Urgences."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('urgences', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
def index():
    return render_template('urgences/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
def api_liste():
    from app.urgences.models import PlanUrgence
    items = PlanUrgence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(PlanUrgence.nom).all()
    return jsonify([{
        'id': i.id, 'nom': i.nom, 'type_urgence': i.type_urgence,
        'description': i.description, 'statut': i.statut,
        'date_derniere_revu': i.date_derniere_revu.isoformat() if i.date_derniere_revu else None,
        'date_prochaine_revu': i.date_prochaine_revu.isoformat() if i.date_prochaine_revu else None,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('urgences')
@has_permission('urgences.voir')
def api_stats():
    from app.urgences.models import PlanUrgence, ExerciceEvacuation, MainCourante
    eid = current_user.entreprise_id
    return jsonify({
        'plans': PlanUrgence.query.filter_by(entreprise_id=eid).count(),
        'exercices': ExerciceEvacuation.query.filter_by(entreprise_id=eid).count(),
        'incidents_ouverts': MainCourante.query.filter_by(entreprise_id=eid, statut='ouvert').count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
def api_creer():
    from app.urgences.models import PlanUrgence
    from datetime import datetime
    data = request.get_json()
    item = PlanUrgence(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), type_urgence=data.get('type_urgence'),
        description=data.get('description'), procedures=data.get('procedures'),
        materiel=data.get('materiel'),
    )
    if data.get('date_derniere_revu'):
        item.date_derniere_revu = datetime.strptime(data['date_derniere_revu'], '%Y-%m-%d').date()
    if data.get('date_prochaine_revu'):
        item.date_prochaine_revu = datetime.strptime(data['date_prochaine_revu'], '%Y-%m-%d').date()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
def api_modifier(item_id):
    from app.urgences.models import PlanUrgence
    item = PlanUrgence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'type_urgence', 'description', 'procedures', 'materiel', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('urgences')
@has_permission('urgences.gerer')
def api_supprimer(item_id):
    from app.urgences.models import PlanUrgence
    item = PlanUrgence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
