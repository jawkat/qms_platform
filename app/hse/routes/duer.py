from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.hse import blueprint
from app.models.hse import UniteTravail, DangerSst, EvaluationRisqueSst
from app.schemas.hse import UniteTravailSchema, DangerSstSchema, EvaluationRisqueSstSchema
from datetime import datetime, date


# --- Pages ---

@blueprint.route('/duer')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def duer():
    return render_template('hse/duer.html')


# --- API: Unités de travail ---

@blueprint.get('/api/unites-travail')
@login_required
@module_access_required('hse', 'hse.voir_duer')
@blueprint.response(200, UniteTravailSchema(many=True))
def api_unites_travail():
    """Liste des unités de travail"""
    return UniteTravail.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(UniteTravail.nom).all()


@blueprint.post('/api/unites-travail/create')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(UniteTravailSchema)
@blueprint.response(201, UniteTravailSchema)
def api_unites_travail_create(data):
    """Créer une unité de travail"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/unites-travail/<int:item_id>/update')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(UniteTravailSchema(partial=True))
@blueprint.response(200, UniteTravailSchema)
def api_unites_travail_update(data, item_id):
    """Mettre à jour une unité de travail"""
    item = UniteTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/unites-travail/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_unites_travail_delete(item_id):
    """Supprimer une unité de travail"""
    item = UniteTravail.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Dangers SST ---

@blueprint.get('/api/dangers-sst')
@login_required
@module_access_required('hse', 'hse.voir_duer')
@blueprint.response(200, DangerSstSchema(many=True))
def api_dangers_sst():
    """Liste des dangers SST"""
    unite_id = request.args.get('unite_travail_id', type=int)
    q = DangerSst.query.filter_by(entreprise_id=current_user.entreprise_id)
    if unite_id:
        q = q.filter_by(unite_travail_id=unite_id)
    return q.order_by(DangerSst.famille_danger, DangerSst.danger).all()


@blueprint.post('/api/dangers-sst/create')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(DangerSstSchema)
@blueprint.response(201, DangerSstSchema)
def api_dangers_sst_create(data):
    """Créer un danger SST"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/dangers-sst/<int:item_id>/update')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(DangerSstSchema(partial=True))
@blueprint.response(200, DangerSstSchema)
def api_dangers_sst_update(data, item_id):
    """Mettre à jour un danger SST"""
    item = DangerSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/dangers-sst/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_dangers_sst_delete(item_id):
    """Supprimer un danger SST"""
    item = DangerSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Évaluations risques SST ---

@blueprint.get('/api/evaluations-risques')
@login_required
@module_access_required('hse', 'hse.voir_duer')
@blueprint.response(200, EvaluationRisqueSstSchema(many=True))
def api_evaluations_risques():
    """Liste des évaluations de risques SST"""
    danger_id = request.args.get('danger_id', type=int)
    q = EvaluationRisqueSst.query.filter_by(entreprise_id=current_user.entreprise_id)
    if danger_id:
        q = q.filter_by(danger_id=danger_id)
    return q.order_by(EvaluationRisqueSst.date_creation.desc()).all()


@blueprint.post('/api/evaluations-risques/create')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(EvaluationRisqueSstSchema)
@blueprint.response(201, EvaluationRisqueSstSchema)
def api_evaluations_risques_create(data):
    """Créer une évaluation de risque SST"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/evaluations-risques/<int:item_id>/update')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
@blueprint.arguments(EvaluationRisqueSstSchema(partial=True))
@blueprint.response(200, EvaluationRisqueSstSchema)
def api_evaluations_risques_update(data, item_id):
    """Mettre à jour une évaluation de risque SST"""
    item = EvaluationRisqueSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/evaluations-risques/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.gerer_duer')
def api_evaluations_risques_delete(item_id):
    """Supprimer une évaluation de risque SST"""
    item = EvaluationRisqueSst.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Statistiques DUER ---

@blueprint.get('/api/duer/stats')
@login_required
@module_access_required('hse', 'hse.voir_duer')
def api_duer_stats():
    """Statistiques DUER"""
    eid = current_user.entreprise_id
    unites = UniteTravail.query.filter_by(entreprise_id=eid).count()
    dangers = DangerSst.query.filter_by(entreprise_id=eid).count()
    evaluations = EvaluationRisqueSst.query.filter_by(entreprise_id=eid).all()
    total_eval = len(evaluations)
    critique = sum(1 for e in evaluations if e.niveau_risque == 'critique')
    eleve = sum(1 for e in evaluations if e.niveau_risque == 'eleve')
    a_traiter = sum(1 for e in evaluations if e.statut == 'a_traiter')
    traite = sum(1 for e in evaluations if e.statut == 'traite')
    return {
        'unites': unites, 'dangers': dangers,
        'evaluations': total_eval,
        'critique': critique, 'eleve': eleve,
        'a_traiter': a_traiter, 'traite': traite,
    }
