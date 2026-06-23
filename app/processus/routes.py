# =============================================================================
# QMS Platform — Processus Routes
# =============================================================================
"""
Routes pour la gestion des processus et la cartographie BPMN.

Ce module gère :
1. Le CRUD des processus (fiches processus)
2. L'import/export de diagrammes BPMN 2.0
3. L'édition visuelle via bpmn.io
4. La synchronisation BPMN ↔ modèle Processus

Auteur : QMS Platform Team
Version : 2.0.0 (BPMN integration)
"""

from flask import render_template, request, jsonify
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app import db
from app.processus import blueprint
from app.models import Processus, IndicateurProcessus
from app.models.auth import Utilisateur
from app.models.indicateurs import Indicateur
from datetime import date, datetime


from app.schemas.processus import ProcessusSchema


class ProcessusResource(BaseResource):
    model = Processus
    schema = ProcessusSchema
    search_fields = ['nom', 'description']
    sort_field = 'nom'
    sort_dir = 'asc'


auto_register_crud(blueprint, Processus, ProcessusSchema,
                   permission_voir='processus.voir', permission_gerer='processus.gerer',
                   flat=True)


@blueprint.route('/')
@access_required(permission='processus.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('processus/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/stats')
@access_required(permission='processus.voir')
def api_stats():
    """Statistiques des processus"""
    base = Processus.query
    today = date.today()
    a_revoir_q = base.filter(Processus.date_prochaine_revu < today)
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'a_revoir': a_revoir_q.count() if base.filter(Processus.date_prochaine_revu.isnot(None)).count() else 0,
        'sous_processus': base.filter(Processus.processus_parent_id.isnot(None)).count(),
    }


# =============================================================================
# BPMN — Import / Export / Édition
# =============================================================================

@blueprint.route('/<int:item_id>/bpmn')
@access_required(permission='processus.voir')
def bpmn_editor(item_id):
    item = Processus.query.filter_by(
        id=item_id
    ).first_or_404()

    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()

    bpmn_xml = None
    if hasattr(item, 'extra_metadata') and item.extra_metadata:
        bpmn_xml = item.extra_metadata.get('bpmn_xml')

    return render_template(
        'processus/bpmn_editor.html',
        processus=item,
        utilisateurs=utilisateurs,
        bpmn_xml=bpmn_xml,
    )


@blueprint.route('/api/<int:item_id>/bpmn', methods=['GET'])
@access_required(permission='processus.voir')
def api_bpmn_get(item_id):
    item = Processus.query.filter_by(
        id=item_id
    ).first_or_404()

    bpmn_xml = None
    if hasattr(item, 'extra_metadata') and item.extra_metadata:
        bpmn_xml = item.extra_metadata.get('bpmn_xml')

    result = {'bpmn_xml': bpmn_xml}

    if bpmn_xml:
        from app.core.bpmn import get_bpmn_service
        service = get_bpmn_service()
        metadata, issues = service.import_bpmn(bpmn_xml)
        result['metadata'] = service.get_process_summary(metadata)
        result['issues'] = issues

    return jsonify(result)


@blueprint.route('/api/<int:item_id>/bpmn', methods=['POST'])
@access_required(permission='processus.gerer')
def api_bpmn_save(item_id):
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id
    ).first_or_404()

    data = request.get_json()
    bpmn_xml = data.get('bpmn_xml', '')

    from app.core.bpmn import get_bpmn_service
    service = get_bpmn_service()
    metadata, issues = service.import_bpmn(bpmn_xml)

    current = dict(item.extra_metadata or {})
    current['bpmn_xml'] = bpmn_xml
    current['bpmn_updated_at'] = datetime.utcnow().isoformat()
    current['bpmn_process_name'] = metadata.process_name
    item.extra_metadata = current
    flag_modified(item, 'extra_metadata')

    db.session.commit()

    return jsonify({
        'success': True,
        'metadata': service.get_process_summary(metadata),
        'issues': issues,
    })


@blueprint.route('/api/<int:item_id>/bpmn/generate', methods=['POST'])
@access_required(permission='processus.gerer')
def api_bpmn_generate(item_id):
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id
    ).first_or_404()

    from app.core.bpmn import get_bpmn_service
    service = get_bpmn_service()

    processus_data = {
        'id': item.id,
        'nom': item.nom,
        'description': item.description,
        'entree': item.entree,
        'sortie': item.sortie,
        'objectifs': item.objectifs,
    }

    bpmn_xml = service.export_bpmn(processus_data)

    current = dict(item.extra_metadata or {})
    current['bpmn_xml'] = bpmn_xml
    current['bpmn_updated_at'] = datetime.utcnow().isoformat()
    current['bpmn_process_name'] = item.nom
    item.extra_metadata = current
    flag_modified(item, 'extra_metadata')

    db.session.commit()

    metadata, issues = service.import_bpmn(bpmn_xml)

    return jsonify({
        'success': True,
        'bpmn_xml': bpmn_xml,
        'metadata': service.get_process_summary(metadata),
    })


@blueprint.route('/api/<int:item_id>/bpmn/import', methods=['POST'])
@access_required(permission='processus.gerer')
def api_bpmn_import(item_id):
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id
    ).first_or_404()

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Fichier invalide'}), 400

    bpmn_xml = file.read().decode('utf-8')

    from app.core.bpmn import get_bpmn_service
    service = get_bpmn_service()
    metadata, issues = service.import_bpmn(bpmn_xml)

    current = dict(item.extra_metadata or {})
    current['bpmn_xml'] = bpmn_xml
    current['bpmn_updated_at'] = datetime.utcnow().isoformat()
    current['bpmn_process_name'] = metadata.process_name
    item.extra_metadata = current
    flag_modified(item, 'extra_metadata')

    if metadata.process_name and not item.description:
        item.description = metadata.process_documentation

    db.session.commit()

    return jsonify({
        'success': True,
        'metadata': service.get_process_summary(metadata),
        'issues': issues,
    })
