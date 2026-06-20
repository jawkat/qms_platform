from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.fournisseurs import blueprint
from app.models.partages import Fournisseur
from app.models.historique_fournisseur import EvaluationFournisseur, HistoriqueFournisseur
from app.models.auth import Utilisateur
from datetime import datetime, date
from sqlalchemy import func


from app.schemas.partages import FournisseurSchema


@blueprint.route('/')
@login_required
@has_permission('fournisseurs.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('fournisseurs/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/liste')
@login_required
@has_permission('fournisseurs.voir')
@blueprint.response(200, FournisseurSchema(many=True))
def api_liste():
    """Liste des fournisseurs"""
    domaine = session.get('domaine', 'hse')
    return Fournisseur.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Fournisseur.date_creation.desc()).all()


@blueprint.get('/api/stats')
@login_required
@has_permission('fournisseurs.voir')
def api_stats():
    """Statistiques fournisseurs"""
    eid = current_user.entreprise_id
    base = Fournisseur.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'qualifies': base.filter_by(qualification='qualifie').count(),
        'audits_programmes': base.filter(Fournisseur.prochain_audit.isnot(None)).count(),
    }


@blueprint.post('/api/creer')
@login_required
@has_permission('fournisseurs.gerer')
@blueprint.arguments(FournisseurSchema)
@blueprint.response(201, FournisseurSchema)
def api_creer(data):
    """Enregistrer un nouveau fournisseur"""
    data.entreprise_id = current_user.entreprise_id
    data.domaine = session.get('domaine', 'hse')
    data.calculer_score_global()
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('fournisseurs.gerer')
@blueprint.arguments(FournisseurSchema(partial=True))
@blueprint.response(200, FournisseurSchema)
def api_modifier(data, item_id):
    """Mettre à jour un fournisseur"""
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    item.calculer_score_global()
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('fournisseurs.gerer')
def api_supprimer(item_id):
    """Supprimer un fournisseur"""
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.post('/api/<int:item_id>/evaluer')
@login_required
@has_permission('fournisseurs.gerer')
def api_evaluer(item_id):
    """Enregistrer une évaluation périodique"""
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    evaluation = EvaluationFournisseur(
        fournisseur_id=item_id,
        date_evaluation=date.today(),
        evaluateur_id=current_user.id,
        score_global=item.score_global,
        commentaire=data.get('commentaire'),
    )
    db.session.add(evaluation)

    historique = HistoriqueFournisseur(
        fournisseur_id=item_id,
        type_evenement='evaluation',
        date_evenement=date.today(),
        description=f'Évaluation score: {item.score_global}',
        score=item.score_global,
        auteur_id=current_user.id,
    )
    db.session.add(historique)
    db.session.commit()
    return {'success': True}
