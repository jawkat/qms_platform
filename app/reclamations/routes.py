from flask import render_template, request, jsonify, session
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
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

    @classmethod
    def _query(cls):
        q = super()._query()
        domaine = session.get('domaine', 'hse')
        return q.filter_by(domaine=domaine)

    @classmethod
    def list_resources(cls):
        q = cls._query()
        for param, col in cls.filter_fields.items():
            val = request.args.get(param)
            if val:
                q = q.filter(getattr(cls.model, col) == val)
        search = request.args.get('q', '').strip()
        if search and cls.search_fields:
            like = f'%{search}%'
            conds = [getattr(cls.model, f).ilike(like) for f in cls.search_fields]
            q = q.filter(db.or_(*conds))
        sort_attr = getattr(cls.model, cls.sort_field)
        if sort_attr is not None:
            order = getattr(sort_attr, cls.sort_dir)
            if order is not None:
                q = q.order_by(order())
        return q.all()


auto_register_crud(blueprint, Reclamation, ReclamationSchema,
                   permission_voir='reclamations.voir', permission_gerer='reclamations.gerer',
                   flat=True)


@blueprint.route('/')
@access_required(permission='reclamations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('reclamations/index.html', utilisateurs=utilisateurs)


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
