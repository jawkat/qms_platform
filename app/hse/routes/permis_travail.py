from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import Incident, EPI, Inspection, PermisTravail
from app.hse import blueprint
from datetime import date, datetime


@blueprint.route('/permis-travail')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def permis_travail():
    return render_template('hse/permis_travail.html')


@blueprint.route('/api/permis-travail')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_permis_travail():
    items = PermisTravail.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(PermisTravail.date_creation.desc()).all()
    return jsonify([_serialize_permis(r) for r in items])


@blueprint.route('/api/permis-travail/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_permis_travail_create():
    data = request.get_json()
    item = PermisTravail(
        entreprise_id=current_user.entreprise_id,
        type_permis=data.get('type_permis', 'generique'),
        date_permis=datetime.strptime(data['date_permis'], '%Y-%m-%d').date() if data.get('date_permis') else date.today(),
        date_debut=datetime.strptime(data['date_debut'], '%Y-%m-%d').date() if data.get('date_debut') else None,
        date_fin=datetime.strptime(data['date_fin'], '%Y-%m-%d').date() if data.get('date_fin') else None,
        lieu=data.get('lieu'),
        intervention_description=data.get('intervention_description'),
        demandant_id=data.get('demandant_id'),
        risques_identifies=data.get('risques_identifies'),
        mesures_preventives=data.get('mesures_preventives'),
        consignes_securite=data.get('consignes_securite'),
        statut=data.get('statut', 'en_attente'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/permis-travail/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_permis_travail_update(item_id):
    item = PermisTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('type_permis', 'lieu', 'intervention_description', 'demandant_id',
              'responsable_securite_id', 'authorizeur_id', 'risques_identifies',
              'mesures_preventives', 'consignes_securite', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    for df in ('date_permis', 'date_debut', 'date_fin'):
        if data.get(df):
            setattr(item, df, datetime.strptime(data[df], '%Y-%m-%d').date())
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/permis-travail/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_permis_travail_delete(item_id):
    item = PermisTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/stats')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_stats():
    eid = current_user.entreprise_id
    return jsonify({
        'incidents_total': Incident.query.filter_by(entreprise_id=eid).count(),
        'incidents_ouverts': Incident.query.filter_by(entreprise_id=eid, statut='ouvert').count(),
        'incidents_accidents': Incident.query.filter_by(entreprise_id=eid, type_incident='accident').count(),
        'incidents_presqu_accidents': Incident.query.filter_by(entreprise_id=eid, type_incident='presqu_accident').count(),
        'epi_total': EPI.query.filter_by(entreprise_id=eid).count(),
        'epi_perimes': EPI.query.filter_by(entreprise_id=eid, statut='perime').count(),
        'inspections_total': Inspection.query.filter_by(entreprise_id=eid).count(),
        'inspections_nc': Inspection.query.filter_by(entreprise_id=eid, statut='NC').count(),
        'permis_total': PermisTravail.query.filter_by(entreprise_id=eid).count(),
        'permis_en_cours': PermisTravail.query.filter_by(entreprise_id=eid, statut='autorise').count(),
    })


def _serialize_permis(r):
    return {
        'id': r.id, 'type_permis': r.type_permis,
        'date_permis': r.date_permis.isoformat() if r.date_permis else None,
        'date_debut': r.date_debut.isoformat() if r.date_debut else None,
        'date_fin': r.date_fin.isoformat() if r.date_fin else None,
        'lieu': r.lieu, 'intervention_description': r.intervention_description,
        'demandant': f'{r.demandant.prenom} {r.demandant.nom}' if r.demandant else '',
        'risques_identifies': r.risques_identifies,
        'mesures_preventives': r.mesures_preventives,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
