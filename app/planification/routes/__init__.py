"""Routes du module Planification."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('planification', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def index():
    return render_template('planification/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def api_liste():
    from app.planification.models import EvenementPlanification
    from datetime import datetime
    items = EvenementPlanification.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(EvenementPlanification.date_debut).all()
    return jsonify([{
        'id': i.id, 'titre': i.titre, 'description': i.description,
        'type_evenement': i.type_evenement, 'lieu': i.lieu,
        'responsable': i.responsable, 'statut': i.statut,
        'date_debut': i.date_debut.isoformat() if i.date_debut else None,
        'date_fin': i.date_fin.isoformat() if i.date_fin else None,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def api_stats():
    from app.planification.models import EvenementPlanification
    from datetime import datetime, timedelta
    eid = current_user.entreprise_id
    base = EvenementPlanification.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'a_venir': base.filter(EvenementPlanification.date_debut >= datetime.utcnow()).count(),
        'terminees': base.filter_by(statut='termine').count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('planification')
@has_permission('planification.gerer')
def api_creer():
    from app.planification.models import EvenementPlanification
    from datetime import datetime
    data = request.get_json()
    item = EvenementPlanification(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'), description=data.get('description'),
        type_evenement=data.get('type_evenement'), lieu=data.get('lieu'),
        responsable=data.get('responsable'),
    )
    if data.get('date_debut'):
        item.date_debut = datetime.fromisoformat(data['date_debut'].replace('Z', '+00:00'))
    if data.get('date_fin'):
        item.date_fin = datetime.fromisoformat(data['date_fin'].replace('Z', '+00:00'))
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('planification')
@has_permission('planification.gerer')
def api_modifier(item_id):
    from app.planification.models import EvenementPlanification
    from datetime import datetime
    item = EvenementPlanification.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'description', 'type_evenement', 'lieu', 'responsable', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/calendrier')
@login_required
@module_active('planification')
@has_permission('planification.voir')
def api_calendrier():
    from app.planification.models import EvenementPlanification
    items = EvenementPlanification.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    couleurs = {
        'audit': '#3b82f6', 'formation': '#10b981', 'inspection': '#f59e0b',
        'maintenance': '#8b5cf6', 'reunion': '#06b6d4', 'echeance': '#ef4444',
    }
    return jsonify([{
        'id': i.id,
        'title': i.titre,
        'start': i.date_debut.isoformat() if i.date_debut else None,
        'end': i.date_fin.isoformat() if i.date_fin else None,
        'color': couleurs.get(i.type_evenement, '#6b7280'),
        'extendedProps': {
            'type': i.type_evenement,
            'lieu': i.lieu,
            'responsable': i.responsable,
            'statut': i.statut,
        },
    } for i in items])


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('planification')
@has_permission('planification.gerer')
def api_supprimer(item_id):
    from app.planification.models import EvenementPlanification
    item = EvenementPlanification.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
