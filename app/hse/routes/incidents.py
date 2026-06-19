from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Incident
from app.hse import blueprint
from datetime import date, datetime


@blueprint.route('/')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def tableau_de_bord():
    return render_template('hse/tableau_de_bord.html')


@blueprint.route('/incidents')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def incidents():
    return render_template('hse/incidents.html')


@blueprint.route('/api/incidents')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_incidents():
    eid = current_user.entreprise_id
    q = Incident.query.filter_by(entreprise_id=eid)
    type_f = request.args.get('type')
    if type_f:
        q = q.filter_by(type_incident=type_f)
    statut = request.args.get('statut')
    if statut:
        q = q.filter_by(statut=statut)
    items = q.order_by(Incident.date_creation.desc()).all()
    return jsonify([_serialize_incident(r) for r in items])


@blueprint.route('/api/incidents/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_incidents_create():
    data = request.get_json()
    item = Incident(
        entreprise_id=current_user.entreprise_id,
        type_incident=data.get('type_incident', 'incident'),
        date_incident=datetime.strptime(data['date_incident'], '%Y-%m-%d').date() if data.get('date_incident') else date.today(),
        lieu=data.get('lieu'), zone=data.get('zone'),
        description=data.get('description', ''),
        victimes=data.get('victimes'), type_blessure=data.get('type_blessure'),
        jours_arret=data.get('jours_arret', 0),
        temoins=data.get('temoins'),
        declarant_id=data.get('declarant_id'),
        cause_initiale=data.get('cause_initiale'),
        statut=data.get('statut', 'ouvert'),
        gravite=data.get('gravite', 'majeur'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/incidents/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_incidents_update(item_id):
    item = Incident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('type_incident', 'lieu', 'zone', 'description', 'victimes', 'type_blessure',
              'jours_arret', 'temoins', 'declarant_id', 'cause_initiale', 'analyse_racine',
              'statut', 'gravite'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_incident'):
        item.date_incident = datetime.strptime(data['date_incident'], '%Y-%m-%d').date()
    if data.get('date_cloture'):
        item.date_cloture = datetime.strptime(data['date_cloture'], '%Y-%m-%d').date()
    if data.get('action_corrective_id'):
        item.action_corrective_id = data['action_corrective_id']
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/incidents/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_incidents_delete(item_id):
    item = Incident.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


def _serialize_incident(r):
    return {
        'id': r.id, 'type_incident': r.type_incident,
        'date_incident': r.date_incident.isoformat() if r.date_incident else None,
        'lieu': r.lieu, 'zone': r.zone, 'description': r.description,
        'victimes': r.victimes, 'type_blessure': r.type_blessure,
        'jours_arret': r.jours_arret, 'temoins': r.temoins,
        'declarant': f'{r.declarant.prenom} {r.declarant.nom}' if r.declarant else '',
        'declarant_id': r.declarant_id,
        'cause_initiale': r.cause_initiale, 'analyse_racine': r.analyse_racine,
        'statut': r.statut, 'gravite': r.gravite,
        'date_cloture': r.date_cloture.isoformat() if r.date_cloture else None,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
