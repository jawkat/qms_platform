from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import RevueDirection
from app.qualite import blueprint
from datetime import date, datetime


@blueprint.route('/revue')
@login_required
@module_access_required('qualite', 'qualite.voir')
def revue():
    return render_template('qualite/revue.html')


@blueprint.route('/api/revue')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_revue():
    items = RevueDirection.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(RevueDirection.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_revue': r.date_revue.isoformat() if r.date_revue else None,
        'participants': r.participants,
        'decisions': r.decisions,
        'suivi': r.suivi,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/revue/create', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_revue_create():
    data = request.get_json()
    date_val = datetime.strptime(data['date_revue'], '%Y-%m-%d').date() if data.get('date_revue') else date.today()
    item = RevueDirection(
        entreprise_id=current_user.entreprise_id,
        date_revue=date_val,
        participants=data.get('participants'),
        decisions=data.get('decisions'),
        suivi=data.get('suivi'),
        statut=data.get('statut', 'realisee'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/revue/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_revue_update(item_id):
    item = RevueDirection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('date_revue'):
        item.date_revue = datetime.strptime(data['date_revue'], '%Y-%m-%d').date()
    item.participants = data.get('participants', item.participants)
    item.decisions = data.get('decisions', item.decisions)
    item.suivi = data.get('suivi', item.suivi)
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/revue/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_revue_delete(item_id):
    item = RevueDirection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
