from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import current_user
from app import db
from app.models import ActionCorrective, ProofMaster, ProofReference, Utilisateur
from app.actions import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.services.quota_middleware import check_quota
from app.services.action_service import ActionService
from app.schemas.actions import ActionSchema, ActionCreateSchema
from datetime import datetime, date
import csv
import io


class ActionCorrectiveResource(BaseResource):
    model = ActionCorrective
    schema = ActionSchema
    search_fields = ['description', 'type_action', 'statut', 'priorite']
    filter_fields = {'statut': 'statut', 'type_action': 'type_action', 'priorite': 'priorite'}
    sort_field = 'date_creation'
    sort_dir = 'desc'


@blueprint.route('/')
@blueprint.route('/')
@blueprint.route('/liste')
@access_required(permission='actions.voir')
def liste_actions():
    actions = ActionService.get_all_by_tenant(
        entreprise_id=current_user.entreprise_id,
        **request.args
    )
    responsables = Utilisateur.query.all()
    return render_template('actions/liste.html', actions=actions, responsables=responsables,
                           filters=request.args)


@blueprint.get('/api/liste')
@access_required(permission='actions.voir')
@blueprint.response(200, ActionSchema(many=True))
def api_liste_actions():
    """Liste des actions au format JSON"""
    return ActionService.get_all_by_tenant(current_user.entreprise_id)


@blueprint.post('/api/create')
@access_required(permission='actions.cree')
@check_quota('actions')
@blueprint.arguments(ActionCreateSchema)
@blueprint.response(201, ActionSchema)
def api_create_action(data):
    """Creer une nouvelle action corrective"""
    data['entreprise_id'] = current_user.entreprise_id
    return ActionService.create(**data)


@blueprint.route('/<int:action_id>', methods=['GET', 'POST'])
@access_required(permission='actions.modifier')
def detail_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    responsables = Utilisateur.query.all()
    if request.method == 'POST':
        action.description = request.form.get('description', action.description)
        action.statut = request.form.get('statut', action.statut)
        action.priorite = request.form.get('priorite', action.priorite)
        action.type_action = request.form.get('type_action', action.type_action)
        action.responsable_id = request.form.get('responsable_id', type=int) or action.responsable_id
        action.cause_identifiee = request.form.get('cause_identifiee')
        if request.form.get('date_echeance'):
            action.date_echeance = datetime.strptime(request.form['date_echeance'], '%Y-%m-%d').date()
        action.est_recurrente = bool(request.form.get('est_recurrente'))
        action.frequence = request.form.get('frequence')
        action.efficacite = request.form.get('efficacite', type=float) or None
        action.commentaire_efficacite = request.form.get('commentaire_efficacite')
        action.critere_efficacite = request.form.get('critere_efficacite')
        action.rca_pourquoi1 = request.form.get('rca_pourquoi1')
        action.rca_pourquoi2 = request.form.get('rca_pourquoi2')
        action.rca_pourquoi3 = request.form.get('rca_pourquoi3')
        action.rca_pourquoi4 = request.form.get('rca_pourquoi4')
        action.rca_pourquoi5 = request.form.get('rca_pourquoi5')
        action.rca_conclusion = request.form.get('rca_conclusion')
        if request.form.get('statut') == 'REALISE' and not action.date_realisation:
            action.date_realisation = date.today()
        db.session.commit()
        flash('Action mise a jour.', 'success')
        return redirect(url_for('actions.detail_action', action_id=action.id))
    return render_template('actions/detail.html', action=action, responsables=responsables)


@blueprint.post('/<int:action_id>/api/update')
@access_required(permission='actions.modifier')
def api_update_action(action_id):
    """Mettre à jour une action via API"""
    data = request.get_json() or {}
    action = ActionService.update(action_id, current_user.entreprise_id, **data)
    if not action:
        return {"message": "Action non trouvée"}, 404
    
    # Logique spéciale pour la date de réalisation
    if data.get('statut') == 'REALISE' and not action.date_realisation:
        action.date_realisation = date.today()
        db.session.commit()
        
    return ActionSchema().dump(action)


from app.schemas.actions import ActionSchema, ActionCreateSchema, ActionReferenceSchema
from app.services.proof_service import ProofService


@blueprint.post('/<int:action_id>/status')
@access_required(permission='actions.modifier')
@blueprint.response(200, ActionSchema)
def update_status(action_id):
    """Mettre à jour le statut d'une action"""
    action = tenant_get_or_404(ActionCorrective, action_id)
    new_status = request.json.get('statut') if request.is_json else request.form.get('statut')
    if new_status:
        action.statut = new_status
        if new_status == 'REALISE':
            action.date_realisation = date.today()
        db.session.commit()
    
    if request.is_json:
        return action
    flash('Statut mis à jour.', 'success')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.post('/<int:action_id>/proof/attach')
@access_required(permission='actions.modifier')
def attach_proof(action_id):
    """Attacher une preuve à une action"""
    action = tenant_get_or_404(ActionCorrective, action_id)
    proof_id = request.json.get('proof_id') if request.is_json else request.form.get('proof_id')
    ref = None
    if proof_id:
        ref = ProofService.attach_proof(
            entreprise_id=current_user.entreprise_id,
            entity_type='action_corrective', entity_id=action.id,
            proof_id=int(proof_id), attached_by=current_user.id,
        )
        db.session.commit()
    
    if request.is_json:
        return {'success': bool(ref), 'reference_id': ref.id if ref else None}
    if ref:
        flash('Preuve attachée.', 'success')
    else:
        flash('Erreur : preuve non trouvée.', 'danger')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.post('/<int:action_id>/proof/detach/<int:ref_id>')
@access_required(permission='actions.modifier')
def detach_proof(action_id, ref_id):
    """Détacher une preuve d'une action"""
    ref = tenant_get_or_404(ProofReference, ref_id)
    ProofService.detach_proof(ref.proof_master_id, ref.entity_type, ref.entity_id)
    db.session.commit()
    return {'success': True}


@blueprint.get('/<int:action_id>/proof/liste')
@access_required(permission='actions.modifier')
@blueprint.response(200, ActionReferenceSchema(many=True))
def list_proofs(action_id):
    """Liste des preuves attachées à une action"""
    action = tenant_get_or_404(ActionCorrective, action_id)
    return ProofReference.query.filter_by(
        entity_type='action_corrective', entity_id=action.id
    ).all()


@blueprint.route('/<int:action_id>/delete', methods=['POST'])
@access_required(permission='actions.supprimer')
def delete_action(action_id):
    action = ActionCorrectiveResource.get_resource(action_id)
    db.session.delete(action)
    db.session.commit()
    flash('Action supprimee.', 'success')
    return redirect(url_for('actions.liste_actions'))


@blueprint.route('/api/export')
@access_required(permission='actions.voir')
def export_actions():
    actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(ActionCorrective.date_creation.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Description', 'Type', 'Priorité', 'Statut', 'Responsable', 'Échéance', 'Créé le'])
    for a in actions:
        writer.writerow([
            a.id,
            a.description or '',
            a.type_action or '',
            a.priorite or '',
            a.statut_label,
            f'{a.responsable.prenom} {a.responsable.nom}' if a.responsable else '',
            a.date_echeance.strftime('%d/%m/%Y') if a.date_echeance else '',
            a.date_creation.strftime('%d/%m/%Y %H:%M') if a.date_creation else '',
        ])

    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=actions_export.csv'}
    )
