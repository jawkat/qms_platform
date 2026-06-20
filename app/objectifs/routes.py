from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.objectifs import blueprint
from app.models.qualite import ObjectifQualite
from datetime import datetime


from app.schemas.objectifs import ObjectifQualiteSchema
from app.models.qualite import ObjectifQualite


@blueprint.route('/')
@login_required
@has_permission('indicateurs.voir')
def index():
    return render_template('objectifs/index.html')


@blueprint.get('/api/liste')
@login_required
@has_permission('indicateurs.voir')
@blueprint.response(200, ObjectifQualiteSchema(many=True))
def api_liste():
    """Liste des objectifs qualité"""
    return ObjectifQualite.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(ObjectifQualite.date_creation.desc()).all()


@blueprint.post('/api/creer')
@login_required
@has_permission('indicateurs.cree')
@blueprint.arguments(ObjectifQualiteSchema)
@blueprint.response(201, ObjectifQualiteSchema)
def api_creer(data):
    """Créer un nouvel objectif"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('indicateurs.modifier')
@blueprint.arguments(ObjectifQualiteSchema(partial=True))
@blueprint.response(200, ObjectifQualiteSchema)
def api_modifier(data, item_id):
    """Modifier un objectif"""
    item = ObjectifQualite.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('indicateurs.modifier')
def api_supprimer(item_id):
    """Supprimer un objectif"""
    item = ObjectifQualite.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.get('/api/stats')
@login_required
@has_permission('indicateurs.voir')
def api_stats():
    """Statistiques des objectifs"""
    eid = current_user.entreprise_id
    base = ObjectifQualite.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'atteint': base.filter_by(statut='atteint').count(),
        'en_retard': base.filter_by(statut='en_retard').count(),
        'non_atteint': base.filter_by(statut='non_atteint').count(),
    }
