from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.workflow_engine import blueprint
from app.workflow_engine.models import WorkflowModele, WorkflowEtape, WorkflowInstance, WorkflowHistorique
from datetime import datetime


@blueprint.route('/')
@login_required
@has_permission('workflow_engine.voir')
def index():
    return render_template('workflow_engine/index.html')


@blueprint.route('/api/modeles')
@login_required
@has_permission('workflow_engine.voir')
def api_modeles():
    items = WorkflowModele.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(WorkflowModele.nom).all()
    return jsonify([{
        'id': m.id, 'nom': m.nom, 'description': m.description,
        'module_cible': m.module_cible, 'statut': m.statut,
        'nb_etapes': m.etapes.count(),
    } for m in items])


@blueprint.route('/api/modeles/create', methods=['POST'])
@login_required
@has_permission('workflow_engine.gerer')
def api_modeles_create():
    data = request.get_json()
    modele = WorkflowModele(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        module_cible=data.get('module_cible', 'documents'),
    )
    db.session.add(modele)
    db.session.flush()

    etapes = data.get('etapes', [])
    for i, e in enumerate(etapes):
        etape = WorkflowEtape(
            modele_id=modele.id,
            nom=e.get('nom'), description=e.get('description'),
            ordre=i + 1, role_requis=e.get('role_requis'),
            action_requise=e.get('action_requise', 'approuver'),
        )
        db.session.add(etape)

    db.session.commit()
    return jsonify({'success': True, 'id': modele.id})


@blueprint.route('/api/modeles/<int:item_id>/delete', methods=['POST'])
@login_required
@has_permission('workflow_engine.gerer')
def api_modeles_delete(item_id):
    item = WorkflowModele.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/instances')
@login_required
@has_permission('workflow_engine.voir')
def api_instances():
    items = WorkflowInstance.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(WorkflowInstance.date_creation.desc()).all()
    return jsonify([{
        'id': i.id, 'modele': i.modele.nom if i.modele else '',
        'entity_type': i.entity_type, 'entity_id': i.entity_id,
        'etape_courante': i.etape_courante.nom if i.etape_courante else '',
        'statut': i.statut,
        'date_debut': i.date_debut.isoformat() if i.date_debut else None,
    } for i in items])


@blueprint.route('/api/instances/<int:item_id>/valider', methods=['POST'])
@login_required
@has_permission('workflow_engine.gerer')
def api_instances_valider(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    if instance.statut != 'en_cours':
        return jsonify({'success': False, 'error': 'Instance non active'})

    data = request.get_json()
    historique = WorkflowHistorique(
        instance_id=instance.id,
        etape_id=instance.etape_courante_id,
        utilisateur_id=current_user.id,
        action='approuver',
        commentaire=data.get('commentaire'),
    )
    db.session.add(historique)

    etapes = list(instance.modele.etapes.order_by(WorkflowEtape.ordre).all())
    current_idx = next((i for i, e in enumerate(etapes) if e.id == instance.etape_courante_id), -1)

    if current_idx < len(etapes) - 1:
        instance.etape_courante_id = etapes[current_idx + 1].id
    else:
        instance.statut = 'termine'
        instance.date_fin = datetime.utcnow()

    db.session.commit()
    return jsonify({'success': True, 'statut': instance.statut})


@blueprint.route('/api/instances/<int:item_id>/rejeter', methods=['POST'])
@login_required
@has_permission('workflow_engine.gerer')
def api_instances_rejeter(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    if instance.statut != 'en_cours':
        return jsonify({'success': False, 'error': 'Instance non active'})

    data = request.get_json()
    historique = WorkflowHistorique(
        instance_id=instance.id,
        etape_id=instance.etape_courante_id,
        utilisateur_id=current_user.id,
        action='rejeter',
        commentaire=data.get('commentaire'),
    )
    db.session.add(historique)
    instance.statut = 'rejete'
    instance.date_fin = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/stats')
@login_required
@has_permission('workflow_engine.voir')
def api_stats():
    eid = current_user.entreprise_id
    return jsonify({
        'modeles': WorkflowModele.query.filter_by(entreprise_id=eid).count(),
        'instances_actives': WorkflowInstance.query.filter_by(entreprise_id=eid, statut='en_cours').count(),
        'instances_terminees': WorkflowInstance.query.filter_by(entreprise_id=eid, statut='termine').count(),
    })
