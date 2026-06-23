from flask import render_template, request, jsonify, session
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.reclamations import blueprint
from app.models.partages import Reclamation
from app.models.auth import Utilisateur
from datetime import date, datetime
from sqlalchemy import func


from app.schemas.partages import ReclamationSchema


class ReclamationResource(BaseResource):
    model = Reclamation
    schema = ReclamationSchema
    search_fields = ['titre', 'description']


@blueprint.route('/')
@access_required(permission='reclamations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('reclamations/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/liste')
@access_required(permission='reclamations.voir')
@blueprint.response(200, ReclamationSchema(many=True))
def api_liste():
    """Liste des réclamations clients"""
    domaine = session.get('domaine', 'hse')
    return Reclamation.query.filter_by(
        domaine=domaine
    ).order_by(Reclamation.date_creation.desc()).all()


@blueprint.get('/api/stats')
@access_required(permission='reclamations.voir')
def api_stats():
    """Statistiques des réclamations"""
    domaine = session.get('domaine', 'hse')
    base = Reclamation.query.filter_by(domaine=domaine)

    par_severite = dict(base.with_entities(Reclamation.severite, func.count())
        .group_by(Reclamation.severite).all())
    par_type = dict(base.with_entities(Reclamation.type_reclamation, func.count())
        .group_by(Reclamation.type_reclamation).all())
    par_statut = dict(base.with_entities(Reclamation.statut, func.count())
        .group_by(Reclamation.statut).all())

    return {
        'total': base.count(),
        'ouvertes': base.filter_by(statut='ouverte').count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'cloturees': base.filter_by(statut='cloturee').count(),
        'par_severite': par_severite,
        'par_type': par_type,
        'par_statut': par_statut,
    }


@blueprint.get('/api/pareto')
@access_required(permission='reclamations.voir')
def api_pareto():
    """Analyse Pareto des réclamations"""
    domaine = session.get('domaine', 'hse')
    rows = db.session.query(
        Reclamation.type_reclamation, func.count()
    ).filter_by(domaine=domaine) \
     .group_by(Reclamation.type_reclamation) \
     .order_by(func.count().desc()).all()

    total = sum(c for _, c in rows)
    cumulative = 0
    result = []
    for label, count in rows:
        cumulative += count
        result.append({
            'type': label or 'Non classifié',
            'count': count,
            'cumulative_pct': round(cumulative / total * 100, 1) if total else 0,
        })
    return result


@blueprint.post('/api/creer')
@access_required(permission='reclamations.gerer')
@blueprint.arguments(ReclamationSchema)
@blueprint.response(201, ReclamationSchema)
def api_creer(data):
    """Déclarer une nouvelle réclamation"""
    return ReclamationResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(permission='reclamations.gerer')
@blueprint.arguments(ReclamationSchema(partial=True))
@blueprint.response(200, ReclamationSchema)
def api_modifier(data, item_id):
    """Mettre à jour une réclamation"""
    return ReclamationResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(permission='reclamations.gerer')
def api_supprimer(item_id):
    """Supprimer une réclamation"""
    return ReclamationResource.delete_resource(item_id)
