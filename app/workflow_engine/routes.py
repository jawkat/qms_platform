from flask import render_template, request, jsonify
from flask_login import current_user
from app.utils.permissions import access_required
from app import db
from app.workflow_engine import blueprint
from app.models import WorkflowModele, WorkflowEtape, WorkflowInstance, WorkflowHistorique
from datetime import datetime
from app.utils.base_resource import BaseResource


class WorkflowModeleResource(BaseResource):
    model = WorkflowModele
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})


class WorkflowInstanceResource(BaseResource):
    model = WorkflowInstance
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})


def _notify_workflow(user_id, message, wf_type='workflow'):
    from app.utils.notifications import create_notification
    create_notification(user_id, message, type=wf_type)


@blueprint.route('/')
@access_required(permission='workflow_engine.voir')
def index():
    return render_template('workflow_engine/index.html')


@blueprint.route('/api/modeles')
@access_required(permission='workflow_engine.voir')
def api_modeles():
    module = request.args.get('module')
    q = WorkflowModele.query.filter_by(statut='actif')
    if module:
        q = q.filter_by(module_cible=module)
    items = q.order_by(WorkflowModele.nom).all()
    return jsonify([m.to_dict() for m in items])


@blueprint.route('/api/modeles/creer', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_modeles_creer():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'Données invalides'}), 400
    nom = (data.get('nom') or '').strip()
    if not nom:
        return jsonify({'success': False, 'error': 'Le nom est obligatoire'}), 400
    modele = WorkflowModele(
        entreprise_id=current_user.entreprise_id,
        nom=nom, description=data.get('description', ''),
        module_cible=data.get('module_cible', 'documents'),
    )
    db.session.add(modele)
    db.session.flush()

    etapes = data.get('etapes', [])
    for i, e in enumerate(etapes):
        etape_nom = (e.get('nom') or '').strip()
        if not etape_nom:
            continue
        etape = WorkflowEtape(
            modele_id=modele.id,
            nom=etape_nom, description=e.get('description', ''),
            ordre=i + 1, role_requis=e.get('role_requis', ''),
            action_requise=e.get('action_requise', 'approuver'),
            delai_jours=e.get('delai_jours'),
        )
        db.session.add(etape)

    db.session.commit()
    return jsonify({'success': True, 'id': modele.id})


@blueprint.route('/api/modeles/<int:item_id>', methods=['GET'])
@access_required(permission='workflow_engine.voir')
def api_modele_detail(item_id):
    modele = WorkflowModele.query.filter_by(
        id=item_id
    ).first_or_404()
    result = modele.to_dict()
    result['etapes'] = [e.to_dict() for e in modele.etapes.order_by(WorkflowEtape.ordre).all()]
    return jsonify(result)


@blueprint.route('/api/modeles/<int:item_id>/supprimer', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_modeles_supprimer(item_id):
    WorkflowModeleResource.delete_resource(item_id)
    return jsonify({'success': True})


@blueprint.route('/api/instances', methods=['GET'])
@access_required(permission='workflow_engine.voir')
def api_instances():
    statut = request.args.get('statut')
    module = request.args.get('module')
    q = WorkflowInstance.query
    if statut:
        q = q.filter_by(statut=statut)
    if module:
        q = q.join(WorkflowModele).filter(WorkflowModele.module_cible == module)
    items = q.order_by(WorkflowInstance.date_creation.desc()).limit(200).all()
    return jsonify([i.to_dict() for i in items])


@blueprint.route('/api/instances/creer', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_instances_creer():
    data = request.get_json()
    modele_id = data.get('modele_id')
    modele = WorkflowModele.query.filter_by(
        id=modele_id
    ).first_or_404()

    etapes = list(modele.etapes.order_by(WorkflowEtape.ordre).all())
    if not etapes:
        return jsonify({'success': False, 'error': 'Le modèle n\'a pas d\'étapes'}), 400

    premiere_etape = etapes[0]
    deadline = None
    if premiere_etape.delai_jours:
        deadline = datetime.utcnow() + __import__('datetime').timedelta(days=premiere_etape.delai_jours)

    instance = WorkflowInstance(
        entreprise_id=current_user.entreprise_id,
        modele_id=modele.id,
        entity_type=data.get('entity_type', modele.module_cible),
        entity_id=data.get('entity_id', 0),
        etape_courante_id=premiere_etape.id,
        demandeur_id=current_user.id,
        statut='en_cours',
        date_deadline=deadline,
        commentaire=data.get('commentaire'),
    )
    db.session.add(instance)
    db.session.flush()

    historique = WorkflowHistorique(
        instance_id=instance.id,
        etape_id=premiere_etape.id,
        utilisateur_id=current_user.id,
        action='creer',
        commentaire='Workflow démarré',
    )
    db.session.add(historique)
    db.session.commit()
    return jsonify({'success': True, 'id': instance.id})


@blueprint.route('/api/instances/<int:item_id>', methods=['GET'])
@access_required(permission='workflow_engine.voir')
def api_instance_detail(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id
    ).first_or_404()
    result = instance.to_dict()
    result['historique'] = [h.to_dict() for h in instance.historique.order_by(WorkflowHistorique.date_action.desc()).all()]
    etapes = list(instance.modele.etapes.order_by(WorkflowEtape.ordre).all())
    result['etapes'] = []
    for e in etapes:
        ed = e.to_dict()
        if instance.etape_courante_id and e.ordre < instance.etape_courante.ordre:
            ed['statut_etape'] = 'termine'
        elif e.id == instance.etape_courante_id:
            ed['statut_etape'] = 'en_cours'
        else:
            ed['statut_etape'] = 'en_attente'
        result['etapes'].append(ed)
    return jsonify(result)


@blueprint.route('/api/instances/<int:item_id>/valider', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_instances_valider(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id
    ).first_or_404()
    if instance.statut != 'en_cours':
        return jsonify({'success': False, 'error': 'Instance non active'}), 400

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
        next_etape = etapes[current_idx + 1]
        instance.etape_courante_id = next_etape.id
        if next_etape.delai_jours:
            instance.date_deadline = datetime.utcnow() + __import__('datetime').timedelta(days=next_etape.delai_jours)
        if instance.demandeur_id:
            _notify_workflow(instance.demandeur_id,
                f'Workflow "{instance.modele.nom}" : étape "{next_etape.nom}" en attente de validation.')
    else:
        instance.statut = 'termine'
        instance.date_fin = datetime.utcnow()
        instance.date_deadline = None
        if instance.demandeur_id:
            _notify_workflow(instance.demandeur_id,
                f'Workflow "{instance.modele.nom}" terminé avec succès.')

    _notify_workflow_workflow_audit(instance, 'approuver', data.get('commentaire'))
    db.session.commit()
    return jsonify({'success': True, 'statut': instance.statut})


@blueprint.route('/api/instances/<int:item_id>/rejeter', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_instances_rejeter(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id
    ).first_or_404()
    if instance.statut != 'en_cours':
        return jsonify({'success': False, 'error': 'Instance non active'}), 400

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
    instance.date_deadline = None

    if instance.demandeur_id:
        _notify_workflow(instance.demandeur_id,
            f'Workflow "{instance.modele.nom}" rejeté à l\'étape "{instance.etape_courante.nom}". Motif : {data.get("commentaire", "")}')

    _notify_workflow_workflow_audit(instance, 'rejeter', data.get('commentaire'))
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/instances/<int:item_id>/annuler', methods=['POST'])
@access_required(permission='workflow_engine.gerer')
def api_instances_annuler(item_id):
    instance = WorkflowInstance.query.filter_by(
        id=item_id
    ).first_or_404()
    if instance.statut != 'en_cours':
        return jsonify({'success': False, 'error': 'Instance non active'}), 400

    data = request.get_json()
    historique = WorkflowHistorique(
        instance_id=instance.id,
        etape_id=instance.etape_courante_id,
        utilisateur_id=current_user.id,
        action='annuler',
        commentaire=data.get('commentaire', 'Workflow annulé'),
    )
    db.session.add(historique)
    instance.statut = 'annule'
    instance.date_fin = datetime.utcnow()
    instance.date_deadline = None
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/stats')
@access_required(permission='workflow_engine.voir')
def api_stats():
    instances_actives = WorkflowInstance.query.filter_by(statut='en_cours')
    now = datetime.utcnow()
    en_retard = sum(1 for i in instances_actives if i.date_deadline and i.date_deadline < now)
    return jsonify({
        'modeles': WorkflowModele.query.filter_by(statut='actif').count(),
        'instances_actives': instances_actives.count(),
        'instances_terminees': WorkflowInstance.query.filter_by(statut='termine').count(),
        'instances_en_retard': en_retard,
    })


@blueprint.route('/api/retard')
@access_required(permission='workflow_engine.voir')
def api_retard():
    now = datetime.utcnow()
    items = WorkflowInstance.query.filter_by(statut='en_cours').all()
    retard = [i.to_dict() for i in items if i.date_deadline and i.date_deadline < now]
    return jsonify(retard)


def _notify_workflow_workflow_audit(instance, action, commentaire):
    from app.models.ged import WorkflowLog as DocWorkflowLog
    from app.models.proofs import ProofMaster
    if instance.entity_type == 'documents':
        proof = ProofMaster.query.get(instance.entity_id)
        if proof:
            log = DocWorkflowLog(
                proof_master_id=proof.id,
                action=f'workflow_{action}',
                commentaire=commentaire,
                utilisateur_id=current_user.id,
                metadata_avant={'workflow_instance_id': instance.id},
            )
            db.session.add(log)
