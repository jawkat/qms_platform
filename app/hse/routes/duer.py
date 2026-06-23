from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.hse import blueprint
from app.models.hse import UniteTravail, DangerSst, EvaluationRisqueSst
from app.schemas.hse import UniteTravailSchema, DangerSstSchema, EvaluationRisqueSstSchema
from datetime import datetime, date


class UniteTravailResource(BaseResource):
    model = UniteTravail
    schema = UniteTravailSchema
    sort_field = 'nom'
    sort_dir = 'asc'


class DangerSstResource(BaseResource):
    model = DangerSst
    schema = DangerSstSchema


class EvaluationRisqueSstResource(BaseResource):
    model = EvaluationRisqueSst
    schema = EvaluationRisqueSstSchema


# --- Pages ---

@blueprint.route('/duer')
@access_required(module='hse', permission='hse.voir_duer')
def duer():
    return render_template('hse/duer.html')


# --- API: Unités de travail ---

@blueprint.get('/api/unites-travail')
@access_required(module='hse', permission='hse.voir_duer')
@blueprint.response(200, UniteTravailSchema(many=True))
def api_unites_travail():
    """Liste des unités de travail"""
    return UniteTravailResource.list_resources()


@blueprint.post('/api/unites-travail/create')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(UniteTravailSchema)
@blueprint.response(201, UniteTravailSchema)
def api_unites_travail_create(data):
    """Créer une unité de travail"""
    return UniteTravailResource.create_resource(data)


@blueprint.post('/api/unites-travail/<int:item_id>/update')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(UniteTravailSchema(partial=True))
@blueprint.response(200, UniteTravailSchema)
def api_unites_travail_update(data, item_id):
    """Mettre à jour une unité de travail"""
    return UniteTravailResource.update_resource(item_id)


@blueprint.post('/api/unites-travail/<int:item_id>/delete')
@access_required(module='hse', permission='hse.gerer_duer')
def api_unites_travail_delete(item_id):
    """Supprimer une unité de travail"""
    return UniteTravailResource.delete_resource(item_id)


# --- API: Dangers SST ---

@blueprint.get('/api/dangers-sst')
@access_required(module='hse', permission='hse.voir_duer')
@blueprint.response(200, DangerSstSchema(many=True))
def api_dangers_sst():
    """Liste des dangers SST"""
    unite_id = request.args.get('unite_travail_id', type=int)
    q = DangerSst.query
    if unite_id:
        q = q.filter_by(unite_travail_id=unite_id)
    return q.order_by(DangerSst.famille_danger, DangerSst.danger).all()


@blueprint.post('/api/dangers-sst/create')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(DangerSstSchema)
@blueprint.response(201, DangerSstSchema)
def api_dangers_sst_create(data):
    """Créer un danger SST"""
    return DangerSstResource.create_resource(data)


@blueprint.post('/api/dangers-sst/<int:item_id>/update')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(DangerSstSchema(partial=True))
@blueprint.response(200, DangerSstSchema)
def api_dangers_sst_update(data, item_id):
    """Mettre à jour un danger SST"""
    return DangerSstResource.update_resource(item_id)


@blueprint.post('/api/dangers-sst/<int:item_id>/delete')
@access_required(module='hse', permission='hse.gerer_duer')
def api_dangers_sst_delete(item_id):
    """Supprimer un danger SST"""
    return DangerSstResource.delete_resource(item_id)


# --- API: Évaluations risques SST ---

@blueprint.get('/api/evaluations-risques')
@access_required(module='hse', permission='hse.voir_duer')
@blueprint.response(200, EvaluationRisqueSstSchema(many=True))
def api_evaluations_risques():
    """Liste des évaluations de risques SST"""
    danger_id = request.args.get('danger_id', type=int)
    q = EvaluationRisqueSst.query
    if danger_id:
        q = q.filter_by(danger_id=danger_id)
    return q.order_by(EvaluationRisqueSst.date_creation.desc()).all()


@blueprint.post('/api/evaluations-risques/create')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(EvaluationRisqueSstSchema)
@blueprint.response(201, EvaluationRisqueSstSchema)
def api_evaluations_risques_create(data):
    """Créer une évaluation de risque SST"""
    return EvaluationRisqueSstResource.create_resource(data)


@blueprint.post('/api/evaluations-risques/<int:item_id>/update')
@access_required(module='hse', permission='hse.gerer_duer')
@blueprint.arguments(EvaluationRisqueSstSchema(partial=True))
@blueprint.response(200, EvaluationRisqueSstSchema)
def api_evaluations_risques_update(data, item_id):
    """Mettre à jour une évaluation de risque SST"""
    return EvaluationRisqueSstResource.update_resource(item_id)


@blueprint.post('/api/evaluations-risques/<int:item_id>/delete')
@access_required(module='hse', permission='hse.gerer_duer')
def api_evaluations_risques_delete(item_id):
    """Supprimer une évaluation de risque SST"""
    return EvaluationRisqueSstResource.delete_resource(item_id)


# --- API: Statistiques DUER ---

@blueprint.get('/api/duer/stats')
@access_required(module='hse', permission='hse.voir_duer')
def api_duer_stats():
    """Statistiques DUER"""
    unites = UniteTravail.query.count()
    dangers = DangerSst.query.count()
    evaluations = EvaluationRisqueSst.query.all()
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
