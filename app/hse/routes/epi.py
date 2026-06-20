from flask import render_template, request
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import EPI
from app.hse import blueprint
from app.schemas.hse import EPISchema
from datetime import datetime


@blueprint.route('/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def epi_liste():
    return render_template('hse/epi.html')


@blueprint.get('/api/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.response(200, EPISchema(many=True))
def api_epi():
    """Liste des EPI (Équipements de Protection Individuelle)"""
    return EPI.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EPI.date_creation.desc()).all()


@blueprint.post('/api/epi/create')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(EPISchema)
@blueprint.response(201, EPISchema)
def api_epi_create(data):
    """Créer un EPI"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/epi/<int:item_id>/update')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
@blueprint.arguments(EPISchema(partial=True))
@blueprint.response(200, EPISchema)
def api_epi_update(data, item_id):
    """Mettre à jour un EPI"""
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/epi/<int:item_id>/delete')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_delete(item_id):
    """Supprimer un EPI"""
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
