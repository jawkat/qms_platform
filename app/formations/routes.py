from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.formations import blueprint
from app.models.partages import Formation
from datetime import datetime


@blueprint.route('/')
@login_required
@module_access_required('formations', 'formations.voir')
def index():
    return render_template('formations/index.html')


@blueprint.route('/api/liste')
@login_required
@module_access_required('formations', 'formations.voir')
def api_liste():
    domaine = session.get('domaine', 'hse')
    items = Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Formation.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'titre': r.titre, 'theme': r.theme,
        'formateur': r.formateur, 'participants': r.participants,
        'duree_heures': r.duree_heures,
        'date_formation': r.date_formation.isoformat() if r.date_formation else None,
        'evaluation': r.evaluation, 'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_access_required('formations', 'formations.gerer')
def api_creer():
    data = request.get_json()
    item = Formation(
        entreprise_id=current_user.entreprise_id,
        domaine=session.get('domaine', 'hse'),
        titre=data.get('titre'), theme=data.get('theme'),
        formateur=data.get('formateur'), participants=data.get('participants'),
        duree_heures=data.get('duree_heures'),
        date_formation=datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
        if data.get('date_formation') else None,
        evaluation=data.get('evaluation'), statut=data.get('statut', 'planifiee'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_access_required('formations', 'formations.gerer')
def api_modifier(item_id):
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'theme', 'formateur', 'participants', 'duree_heures',
              'evaluation', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_formation'):
        item.date_formation = datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_access_required('formations', 'formations.gerer')
def api_supprimer(item_id):
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
