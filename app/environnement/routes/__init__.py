"""Routes du module Environnement (ISO 14001)."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db
from datetime import datetime

import os
blueprint = Blueprint('environnement', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
def index():
    return render_template('environnement/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
def api_liste():
    from app.environnement.models import AspectEnvironnemental
    items = AspectEnvironnemental.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(AspectEnvironnemental.nom).all()
    return jsonify([{
        'id': i.id, 'nom': i.nom, 'description': i.description,
        'categorie': i.categorie, 'impact': i.impact, 'gravite': i.gravite,
        'maitrise': i.maitrise, 'responsable': i.responsable, 'statut': i.statut,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('environnement')
@has_permission('environnement.voir')
def api_stats():
    from app.environnement.models import AspectEnvironnemental, SuiviEnvironnemental
    eid = current_user.entreprise_id
    return jsonify({
        'total_aspects': AspectEnvironnemental.query.filter_by(entreprise_id=eid).count(),
        'critiques': AspectEnvironnemental.query.filter_by(entreprise_id=eid, gravite='critique').count(),
        'suivis': SuiviEnvironnemental.query.filter_by(entreprise_id=eid).count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
def api_creer():
    from app.environnement.models import AspectEnvironnemental
    data = request.get_json()
    item = AspectEnvironnemental(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        categorie=data.get('categorie'), impact=data.get('impact'),
        gravite=data.get('gravite', 'moyenne'), maitrise=data.get('maitrise'),
        responsable=data.get('responsable'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
def api_modifier(item_id):
    from app.environnement.models import AspectEnvironnemental
    item = AspectEnvironnemental.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'description', 'categorie', 'impact', 'gravite', 'maitrise', 'responsable', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('environnement')
@has_permission('environnement.gerer')
def api_supprimer(item_id):
    from app.environnement.models import AspectEnvironnemental
    item = AspectEnvironnemental.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
