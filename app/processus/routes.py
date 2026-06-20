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
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.processus import blueprint
from app.models import Processus, IndicateurProcessus
from app.models.auth import Utilisateur
from app.models.indicateurs import Indicateur
from datetime import date, datetime


from app.schemas.processus import ProcessusSchema


@blueprint.route('/')
@login_required
@has_permission('processus.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('processus/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/liste')
@login_required
@has_permission('processus.voir')
@blueprint.response(200, ProcessusSchema(many=True))
def api_liste():
    """Liste des processus"""
    return Processus.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Processus.nom).all()


@blueprint.get('/api/stats')
@login_required
@has_permission('processus.voir')
def api_stats():
    """Statistiques des processus"""
    eid = current_user.entreprise_id
    base = Processus.query.filter_by(entreprise_id=eid)
    today = date.today()
    a_revoir_q = base.filter(Processus.date_prochaine_revu < today)
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'a_revoir': a_revoir_q.count() if base.filter(Processus.date_prochaine_revu.isnot(None)).count() else 0,
        'sous_processus': base.filter(Processus.processus_parent_id.isnot(None)).count(),
    }


@blueprint.post('/api/creer')
@login_required
@has_permission('processus.gerer')
@blueprint.arguments(ProcessusSchema)
@blueprint.response(201, ProcessusSchema)
def api_creer(data):
    """Créer un nouveau processus"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('processus.gerer')
@blueprint.arguments(ProcessusSchema(partial=True))
@blueprint.response(200, ProcessusSchema)
def api_modifier(data, item_id):
    """Modifier un processus"""
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('processus.gerer')
def api_supprimer(item_id):
    """Supprimer un processus"""
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# =============================================================================
# BPMN — Import / Export / Édition
# =============================================================================

@blueprint.route('/<int:item_id>/bpmn')
@login_required
@has_permission('processus.voir')
def bpmn_editor(item_id):
    """
    Affiche l'éditeur BPMN unifié pour un processus.

    Interface combinée : éditeur BPMN + fiche processus + indicateurs.
    L'utilisateur peut tout éditer depuis un seul écran.
    """
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()

    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
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
@login_required
@has_permission('processus.voir')
def api_bpmn_get(item_id):
    """
    Récupère le diagramme BPMN d'un processus.

    Returns:
        JSON avec bpmn_xml et les métadonnées extraites
    """
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()

    bpmn_xml = None
    if hasattr(item, 'extra_metadata') and item.extra_metadata:
        bpmn_xml = item.extra_metadata.get('bpmn_xml')

    result = {'bpmn_xml': bpmn_xml}

    # Extraire les métadonnées si le XML existe
    if bpmn_xml:
        from app.core.bpmn import get_bpmn_service
        service = get_bpmn_service()
        metadata, issues = service.import_bpmn(bpmn_xml)
        result['metadata'] = service.get_process_summary(metadata)
        result['issues'] = issues

    return jsonify(result)


@blueprint.route('/api/<int:item_id>/bpmn', methods=['POST'])
@login_required
@has_permission('processus.gerer')
def api_bpmn_save(item_id):
    """
    Sauvegarde le diagramme BPMN d'un processus.

    Reçoit le XML BPMN édité via bpmn.io et le sauvegarde
    dans les métadonnées du processus.
    """
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()

    data = request.get_json()
    bpmn_xml = data.get('bpmn_xml', '')

    # Valider le XML
    from app.core.bpmn import get_bpmn_service
    service = get_bpmn_service()
    metadata, issues = service.import_bpmn(bpmn_xml)

    # Sauvegarder dans les métadonnées — assigner un NOUVEAU dict pour que
    # SQLAlchemy détecte le changement sur la colonne JSON
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
@login_required
@has_permission('processus.gerer')
def api_bpmn_generate(item_id):
    """
    Génère un diagramme BPMN à partir des données du processus.

    Crée un diagramme de base basé sur les champs du processus
    (nom, entrée, sortie, objectifs).
    """
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
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

    # Sauvegarder — nouveau dict pour SQLAlchemy
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
@login_required
@has_permission('processus.gerer')
def api_bpmn_import(item_id):
    """
    Importe un fichier BPMN et le associe à un processus.

    Accepte un fichier .bnm ou .xml contenant du BPMN 2.0.
    Extrait les métadonnées et les sauvegarde.
    """
    from sqlalchemy.orm.attributes import flag_modified

    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
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

    # Sauvegarder — nouveau dict pour SQLAlchemy
    current = dict(item.extra_metadata or {})
    current['bpmn_xml'] = bpmn_xml
    current['bpmn_updated_at'] = datetime.utcnow().isoformat()
    current['bpmn_process_name'] = metadata.process_name
    item.extra_metadata = current
    flag_modified(item, 'extra_metadata')

    # Mettre à jour le nom du processus si le BPMN a un nom
    if metadata.process_name and not item.description:
        item.description = metadata.process_documentation

    db.session.commit()

    return jsonify({
        'success': True,
        'metadata': service.get_process_summary(metadata),
        'issues': issues,
    })
