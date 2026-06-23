from flask import render_template, request, jsonify, redirect, url_for
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models import RevueDirection
from app.qualite import blueprint
from app.schemas.qualite import RevueDirectionSchema
from datetime import date, datetime


class RevueDirectionResource(BaseResource):
    model = RevueDirection
    schema = RevueDirectionSchema
    search_fields = ['participants', 'decisions']
    filter_fields = {'statut': 'statut'}


@blueprint.route('/revue')
@access_required(module='qualite', permission='qualite.voir')
def revue():
    return render_template('qualite/revue.html')


@blueprint.route('/api/revue')
@access_required(module='qualite', permission='qualite.voir')
def api_revue():
    items = RevueDirectionResource.list_resources()
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
@access_required(module='qualite', permission='qualite.voir')
def api_revue_create():
    data = request.get_json()
    date_val = datetime.strptime(data['date_revue'], '%Y-%m-%d').date() if data.get('date_revue') else date.today()
    item = RevueDirection(
        date_revue=date_val,
        participants=data.get('participants'),
        decisions=data.get('decisions'),
        suivi=data.get('suivi'),
        statut=data.get('statut', 'realisee'),
    )
    RevueDirectionResource.create_resource(item)
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/revue/<int:item_id>/update', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_revue_update(item_id):
    item = RevueDirectionResource.get_resource(item_id)
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
@access_required(module='qualite', permission='qualite.voir')
def api_revue_delete(item_id):
    RevueDirectionResource.delete_resource(item_id)
    return jsonify({'success': True})
