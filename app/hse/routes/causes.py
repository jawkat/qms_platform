from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.hse import blueprint
from app.models.hse import Incident, CauseIncident
from datetime import datetime


# --- Page ---

@blueprint.route('/incidents/<int:incident_id>/causes')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def arbre_causes(incident_id):
    incident = Incident.query.filter_by(id=incident_id, entreprise_id=current_user.entreprise_id).first_or_404()
    return render_template('hse/causes.html', incident=incident)


# --- API: Causes d'un incident ---

@blueprint.route('/api/incidents/<int:incident_id>/causes')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_causes(incident_id):
    items = CauseIncident.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        incident_id=incident_id,
    ).order_by(CauseIncident.ordre).all()

    def serialize(c):
        return {
            'id': c.id, 'parent_id': c.parent_id,
            'categorie': c.categorie, 'description': c.description,
            'ordre': c.ordre, 'date_creation': c.date_creation.isoformat() if c.date_creation else None,
            'enfants': [serialize(e) for e in c.enfants.order_by(CauseIncident.ordre).all()],
        }

    return jsonify([serialize(c) for c in items if c.parent_id is None])


@blueprint.route('/api/incidents/<int:incident_id>/causes/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
def api_causes_create(incident_id):
    data = request.get_json()
    item = CauseIncident(
        entreprise_id=current_user.entreprise_id,
        incident_id=incident_id,
        parent_id=data.get('parent_id'),
        categorie=data.get('categorie', 'autre'),
        description=data.get('description'),
        ordre=data.get('ordre', 0),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/causes/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
def api_causes_update(item_id):
    item = CauseIncident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('parent_id', 'categorie', 'description', 'ordre'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/causes/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_incidents')
def api_causes_delete(item_id):
    item = CauseIncident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
