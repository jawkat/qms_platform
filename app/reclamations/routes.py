from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.reclamations import blueprint
from app.models.partages import Reclamation
from app.models.auth import Utilisateur
from datetime import date, datetime
from sqlalchemy import func


from app.schemas.partages import ReclamationSchema


@blueprint.route('/')
@login_required
@has_permission('reclamations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('reclamations/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/liste')
@login_required
@has_permission('reclamations.voir')
@blueprint.response(200, ReclamationSchema(many=True))
def api_liste():
    """Liste des réclamations clients"""
    domaine = session.get('domaine', 'hse')
    return Reclamation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Reclamation.date_creation.desc()).all()


@blueprint.get('/api/stats')
@login_required
@has_permission('reclamations.voir')
def api_stats():
    """Statistiques des réclamations"""
    eid = current_user.entreprise_id
    domaine = session.get('domaine', 'hse')
    base = Reclamation.query.filter_by(entreprise_id=eid, domaine=domaine)

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
@login_required
@has_permission('reclamations.voir')
def api_pareto():
    """Analyse Pareto des réclamations"""
    eid = current_user.entreprise_id
    domaine = session.get('domaine', 'hse')
    rows = db.session.query(
        Reclamation.type_reclamation, func.count()
    ).filter_by(entreprise_id=eid, domaine=domaine) \
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
@login_required
@has_permission('reclamations.gerer')
@blueprint.arguments(ReclamationSchema)
@blueprint.response(201, ReclamationSchema)
def api_creer(data):
    """Déclarer une nouvelle réclamation"""
    data.entreprise_id = current_user.entreprise_id
    data.domaine = session.get('domaine', 'hse')
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('reclamations.gerer')
@blueprint.arguments(ReclamationSchema(partial=True))
@blueprint.response(200, ReclamationSchema)
def api_modifier(data, item_id):
    """Mettre à jour une réclamation"""
    item = Reclamation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('reclamations.gerer')
def api_supprimer(item_id):
    """Supprimer une réclamation"""
    item = Reclamation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
