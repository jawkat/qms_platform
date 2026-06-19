from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.entreprise import Entreprise
from app.models.hse import Incident, EPI, Inspection, InspectionItem, PermisTravail
from app.hse import blueprint
from datetime import date, datetime




# --- Dashboard ---

@blueprint.route('/')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def tableau_de_bord():
    return render_template('hse/tableau_de_bord.html')


# --- Incidents ---

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


# --- EPI ---

@blueprint.route('/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def epi_liste():
    return render_template('hse/epi.html')


@blueprint.route('/api/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi():
    items = EPI.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EPI.date_creation.desc()).all()
    return jsonify([_serialize_epi(r) for r in items])


@blueprint.route('/api/epi/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_create():
    data = request.get_json()
    item = EPI(
        entreprise_id=current_user.entreprise_id,
        type_epi=data.get('type_epi', 'autre'),
        designation=data.get('designation', ''),
        marque=data.get('marque'), modele=data.get('modele'),
        numero_serie=data.get('numero_serie'),
        norme_reference=data.get('norme_reference'),
        date_fabrication=datetime.strptime(data['date_fabrication'], '%Y-%m-%d').date() if data.get('date_fabrication') else None,
        date_peremption=datetime.strptime(data['date_peremption'], '%Y-%m-%d').date() if data.get('date_peremption') else None,
        duree_vie_mois=data.get('duree_vie_mois'),
        statut=data.get('statut', 'en_service'),
        utilisateur_affecte_id=data.get('utilisateur_affecte_id'),
        stock_emplacement=data.get('stock_emplacement'),
        prochain_controle=datetime.strptime(data['prochain_controle'], '%Y-%m-%d').date() if data.get('prochain_controle') else None,
        certificat_conformite=data.get('certificat_conformite', False),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/epi/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_update(item_id):
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('type_epi', 'designation', 'marque', 'modele', 'numero_serie',
              'norme_reference', 'duree_vie_mois', 'statut', 'utilisateur_affecte_id',
              'stock_emplacement', 'certificat_conformite'):
        if f in data:
            setattr(item, f, data[f])
    for df in ('date_fabrication', 'date_peremption', 'prochain_controle'):
        if data.get(df):
            setattr(item, df, datetime.strptime(data[df], '%Y-%m-%d').date())
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/epi/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_delete(item_id):
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- Inspections ---

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


# --- Permis de travail ---

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


# --- Stats ---

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


# --- Serializers ---

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


def _serialize_epi(r):
    return {
        'id': r.id, 'type_epi': r.type_epi, 'designation': r.designation,
        'marque': r.marque, 'modele': r.modele, 'numero_serie': r.numero_serie,
        'norme_reference': r.norme_reference,
        'date_fabrication': r.date_fabrication.isoformat() if r.date_fabrication else None,
        'date_peremption': r.date_peremption.isoformat() if r.date_peremption else None,
        'statut': r.statut,
        'utilisateur_affecte': f'{r.utilisateur_affecte.prenom} {r.utilisateur_affecte.nom}' if r.utilisateur_affecte else '',
        'stock_emplacement': r.stock_emplacement,
        'prochain_controle': r.prochain_controle.isoformat() if r.prochain_controle else None,
        'certificat_conformite': r.certificat_conformite,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }


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
