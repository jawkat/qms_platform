"""Routes du module Réunions."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('reunions', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
def index():
    return render_template('reunions/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
def api_liste():
    from app.reunions.models import Reunion
    items = Reunion.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Reunion.date_reunion.desc()).all()
    return jsonify([{
        'id': i.id, 'titre': i.titre, 'type_reunion': i.type_reunion,
        'description': i.description, 'lieu': i.lieu,
        'organisateur': i.organisateur, 'participants': i.participants,
        'statut': i.statut,
        'date_reunion': i.date_reunion.isoformat() if i.date_reunion else None,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('reunions')
@has_permission('reunions.voir')
def api_stats():
    from app.reunions.models import Reunion, ActionReunion
    from datetime import datetime
    eid = current_user.entreprise_id
    return jsonify({
        'total': Reunion.query.filter_by(entreprise_id=eid).count(),
        'a_venir': Reunion.query.filter(Reunion.entreprise_id == eid, Reunion.date_reunion >= datetime.utcnow()).count(),
        'actions_ouvertes': ActionReunion.query.filter_by(entreprise_id=eid, statut='a_faire').count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
def api_creer():
    from app.reunions.models import Reunion
    from datetime import datetime
    data = request.get_json()
    item = Reunion(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'), type_reunion=data.get('type_reunion'),
        description=data.get('description'), lieu=data.get('lieu'),
        organisateur=data.get('organisateur'), participants=data.get('participants'),
    )
    if data.get('date_reunion'):
        item.date_reunion = datetime.fromisoformat(data['date_reunion'].replace('Z', '+00:00'))
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
def api_modifier(item_id):
    from app.reunions.models import Reunion
    item = Reunion.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'type_reunion', 'description', 'lieu', 'organisateur', 'participants', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('reunions')
@has_permission('reunions.gerer')
def api_supprimer(item_id):
    from app.reunions.models import Reunion
    item = Reunion.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
