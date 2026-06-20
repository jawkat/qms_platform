from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.hse import blueprint
from app.models.hse import UniteTravail, DangerSst, EvaluationRisqueSst
from datetime import datetime, date


# --- Pages ---

@blueprint.route('/duer')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def duer():
    return render_template('hse/duer.html')


# --- API: Unités de travail ---

@blueprint.route('/api/unites-travail')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def api_unites_travail():
    items = UniteTravail.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(UniteTravail.nom).all()
    return jsonify([{
        'id': r.id, 'nom': r.nom, 'description': r.description,
        'service': r.service, 'effectif': r.effectif, 'horaires': r.horaires,
        'statut': r.statut, 'nb_dangers': r.dangers.count(),
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/unites-travail/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_unites_travail_create():
    data = request.get_json()
    item = UniteTravail(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        service=data.get('service'), effectif=data.get('effectif', 0),
        horaires=data.get('horaires'), statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/unites-travail/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_unites_travail_update(item_id):
    item = UniteTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('nom', 'description', 'service', 'effectif', 'horaires', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/unites-travail/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_unites_travail_delete(item_id):
    item = UniteTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Dangers SST ---

@blueprint.route('/api/dangers-sst')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def api_dangers_sst():
    unite_id = request.args.get('unite_travail_id', type=int)
    q = DangerSst.query.filter_by(entreprise_id=current_user.entreprise_id)
    if unite_id:
        q = q.filter_by(unite_travail_id=unite_id)
    items = q.order_by(DangerSst.famille_danger, DangerSst.danger).all()
    return jsonify([{
        'id': r.id, 'unite_travail_id': r.unite_travail_id,
        'famille_danger': r.famille_danger, 'danger': r.danger,
        'description': r.description, 'source': r.source,
        'consequence': r.consequence, 'mesures_existantes': r.mesures_existantes,
        'statut': r.statut,
        'unite_nom': r.unite_travail.nom if r.unite_travail else '',
        'nb_evaluations': r.evaluations.count(),
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/dangers-sst/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_dangers_sst_create():
    data = request.get_json()
    item = DangerSst(
        entreprise_id=current_user.entreprise_id,
        unite_travail_id=data.get('unite_travail_id'),
        famille_danger=data.get('famille_danger'),
        danger=data.get('danger'), description=data.get('description'),
        source=data.get('source'), consequence=data.get('consequence'),
        mesures_existantes=data.get('mesures_existantes'),
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/dangers-sst/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_dangers_sst_update(item_id):
    item = DangerSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('unite_travail_id', 'famille_danger', 'danger', 'description',
              'source', 'consequence', 'mesures_existantes', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dangers-sst/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_dangers_sst_delete(item_id):
    item = DangerSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Évaluations risques SST ---

@blueprint.route('/api/evaluations-risques')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def api_evaluations_risques():
    danger_id = request.args.get('danger_id', type=int)
    q = EvaluationRisqueSst.query.filter_by(entreprise_id=current_user.entreprise_id)
    if danger_id:
        q = q.filter_by(danger_id=danger_id)
    items = q.order_by(EvaluationRisqueSst.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'danger_id': r.danger_id,
        'gravite': r.gravite, 'probabilite': r.probabilite,
        'frequence': r.frequence, 'maitrise': r.maitrise,
        'criticite': r.criticite, 'niveau_risque': r.niveau_risque,
        'plan_action': r.plan_action, 'responsable_id': r.responsable_id,
        'date_echeance': r.date_echeance.isoformat() if r.date_echeance else None,
        'date_revu': r.date_revu.isoformat() if r.date_revu else None,
        'statut': r.statut,
        'danger_libelle': r.danger_sst.danger if r.danger_sst else '',
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/evaluations-risques/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_evaluations_risques_create():
    data = request.get_json()
    item = EvaluationRisqueSst(
        entreprise_id=current_user.entreprise_id,
        danger_id=data.get('danger_id'),
        gravite=data.get('gravite', 1),
        probabilite=data.get('probabilite', 1),
        frequence=data.get('frequence', 1),
        maitrise=data.get('maitrise', 1),
        plan_action=data.get('plan_action'),
        responsable_id=data.get('responsable_id'),
        date_echeance=datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
        if data.get('date_echeance') else None,
        statut=data.get('statut', 'a_traiter'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/evaluations-risques/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_evaluations_risques_update(item_id):
    item = EvaluationRisqueSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('danger_id', 'gravite', 'probabilite', 'frequence', 'maitrise',
              'plan_action', 'responsable_id', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_echeance'):
        item.date_echeance = datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
    if data.get('date_revu'):
        item.date_revu = datetime.strptime(data['date_revu'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/evaluations-risques/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_evaluations_risques_delete(item_id):
    item = EvaluationRisqueSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Statistiques DUER ---

@blueprint.route('/api/duer/stats')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def api_duer_stats():
    eid = current_user.entreprise_id
    unites = UniteTravail.query.filter_by(entreprise_id=eid).count()
    dangers = DangerSst.query.filter_by(entreprise_id=eid).count()
    evaluations = EvaluationRisqueSst.query.filter_by(entreprise_id=eid).all()
    total_eval = len(evaluations)
    critique = sum(1 for e in evaluations if e.niveau_risque == 'critique')
    eleve = sum(1 for e in evaluations if e.niveau_risque == 'eleve')
    a_traiter = sum(1 for e in evaluations if e.statut == 'a_traiter')
    traite = sum(1 for e in evaluations if e.statut == 'traite')
    return jsonify({
        'unites': unites, 'dangers': dangers,
        'evaluations': total_eval,
        'critique': critique, 'eleve': eleve,
        'a_traiter': a_traiter, 'traite': traite,
    })
