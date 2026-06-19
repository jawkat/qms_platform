from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Inspection, InspectionItem
from app.hse import blueprint
from datetime import date, datetime


@blueprint.route('/inspections')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def inspections():
    return render_template('hse/inspections.html')


@blueprint.route('/api/inspections')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_inspections():
    items = Inspection.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Inspection.date_creation.desc()).all()
    return jsonify([_serialize_inspection(r) for r in items])


@blueprint.route('/api/inspections/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_inspections_create():
    data = request.get_json()
    item = Inspection(
        entreprise_id=current_user.entreprise_id,
        type_inspection=data.get('type_inspection', 'quotidienne'),
        date_inspection=datetime.strptime(data['date_inspection'], '%Y-%m-%d').date() if data.get('date_inspection') else date.today(),
        lieu=data.get('lieu'), zone=data.get('zone'),
        inspecteur_id=data.get('inspecteur_id'),
        observations=data.get('observations'),
        statut=data.get('statut', 'en_cours'),
    )
    db.session.add(item)
    db.session.flush()
    for ci in data.get('checklist', []):
        item.items.append(InspectionItem(
            checklist_item=ci.get('item', ''),
            conforme=ci.get('conforme'),
            observation=ci.get('observation'),
        ))
    anomalies = sum(1 for it in item.items if it.conforme is False)
    item.anomalies_detectees = anomalies
    if anomalies > 0:
        item.statut = 'NC'
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/inspections/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_inspections_update(item_id):
    item = Inspection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('type_inspection', 'lieu', 'zone', 'inspecteur_id', 'observations', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_inspection'):
        item.date_inspection = datetime.strptime(data['date_inspection'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/inspections/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_inspections_delete(item_id):
    item = Inspection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


def _serialize_inspection(r):
    return {
        'id': r.id, 'type_inspection': r.type_inspection,
        'date_inspection': r.date_inspection.isoformat() if r.date_inspection else None,
        'lieu': r.lieu, 'zone': r.zone,
        'inspecteur': f'{r.inspecteur.prenom} {r.inspecteur.nom}' if r.inspecteur else '',
        'observations': r.observations,
        'anomalies_detectees': r.anomalies_detectees,
        'statut': r.statut,
        'items': [{'id': it.id, 'item': it.checklist_item, 'conforme': it.conforme, 'observation': it.observation} for it in r.items],
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
