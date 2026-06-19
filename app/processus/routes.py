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
from app.processus.models import Processus, IndicateurProcessus
from app.models.auth import Utilisateur
from app.models.indicateurs import Indicateur
from datetime import date, datetime


@blueprint.route('/')
@login_required
@has_permission('processus.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('processus/index.html', utilisateurs=utilisateurs)


@blueprint.route('/api/liste')
@login_required
@has_permission('processus.voir')
def api_liste():
    items = Processus.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Processus.nom).all()
    return jsonify([{
        'id': r.id, 'nom': r.nom, 'description': r.description,
        'type_processus': r.type_processus,
        'proprietaire': f'{r.proprietaire.prenom} {r.proprietaire.nom}' if r.proprietaire else '',
        'proprietaire_id': r.proprietaire_id,
        'processus_parent_id': r.processus_parent_id,
        'entree': r.entree, 'sortie': r.sortie,
        'objectifs': r.objectifs, 'statut': r.statut,
        'date_derniere_revu': r.date_derniere_revu.isoformat() if r.date_derniere_revu else None,
        'date_prochaine_revu': r.date_prochaine_revu.isoformat() if r.date_prochaine_revu else None,
    } for r in items])


@blueprint.route('/api/stats')
@login_required
@has_permission('processus.voir')
def api_stats():
    eid = current_user.entreprise_id
    base = Processus.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'a_revoir': base.filter(Processus.date_prochaine_revu < date.today()).count() if base.filter(Processus.date_prochaine_revu.isnot(None)).count() else 0,
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('processus.gerer')
def api_creer():
    data = request.get_json()
    item = Processus(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        type_processus=data.get('type_processus', 'operationnel'),
        proprietaire_id=data.get('proprietaire_id'),
        processus_parent_id=data.get('processus_parent_id'),
        entree=data.get('entree'), sortie=data.get('sortie'),
        objectifs=data.get('objectifs'), statut=data.get('statut', 'actif'),
    )
    if data.get('date_prochaine_revu'):
        item.date_prochaine_revu = datetime.strptime(data['date_prochaine_revu'], '%Y-%m-%d').date()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('processus.gerer')
def api_modifier(item_id):
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'description', 'type_processus', 'proprietaire_id',
              'processus_parent_id', 'entree', 'sortie', 'objectifs',
              'risques_associes', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_derniere_revu'):
        item.date_derniere_revu = datetime.strptime(data['date_derniere_revu'], '%Y-%m-%d').date()
    if data.get('date_prochaine_revu'):
        item.date_prochaine_revu = datetime.strptime(data['date_prochaine_revu'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('processus.gerer')
def api_supprimer(item_id):
    item = Processus.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


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
