"""Routes du module Connaissances."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

import os
blueprint = Blueprint('connaissances', __name__, template_folder='templates',
                      root_path=os.path.join(os.path.dirname(os.path.dirname(__file__))))


@blueprint.route('/')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
def index():
    return render_template('connaissances/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
def api_liste():
    from app.connaissances.models import REX
    items = REX.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(REX.date_creation.desc()).all()
    return jsonify([{
        'id': i.id, 'titre': i.titre, 'description': i.description,
        'categorie': i.categorie, 'auteur': i.auteur,
        'lecons_apprises': i.lecons_apprises, 'statut': i.statut,
        'date_rex': i.date_rex.isoformat() if i.date_rex else None,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('connaissances')
@has_permission('connaissances.voir')
def api_stats():
    from app.connaissances.models import REX, FAQ
    eid = current_user.entreprise_id
    return jsonify({
        'rex_total': REX.query.filter_by(entreprise_id=eid).count(),
        'rex_publies': REX.query.filter_by(entreprise_id=eid, statut='publie').count(),
        'faq': FAQ.query.filter_by(entreprise_id=eid).count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
def api_creer():
    from app.connaissances.models import REX
    from datetime import datetime
    data = request.get_json()
    item = REX(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'), description=data.get('description'),
        categorie=data.get('categorie'), contexte=data.get('contexte'),
        causes=data.get('causes'), actions_menees=data.get('actions_menees'),
        resultats=data.get('resultats'), lecons_apprises=data.get('lecons_apprises'),
        auteur=data.get('auteur'),
    )
    if data.get('date_rex'):
        item.date_rex = datetime.strptime(data['date_rex'], '%Y-%m-%d').date()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
def api_modifier(item_id):
    from app.connaissances.models import REX
    item = REX.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'description', 'categorie', 'contexte', 'causes', 'actions_menees', 'resultats', 'lecons_apprises', 'auteur', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('connaissances')
@has_permission('connaissances.gerer')
def api_supprimer(item_id):
    from app.connaissances.models import REX
    item = REX.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
