from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import ActionCorrective, ProofMaster, ProofReference
from app.actions import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.services.proof_service import ProofService
from datetime import datetime


@blueprint.route('/liste')
@login_required
def liste_actions():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(ActionCorrective.date_creation.desc()).all()
    return render_template('actions/liste.html', actions=actions, domaine=domaine)


@blueprint.route('/api/liste')
@login_required
def api_liste_actions():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(ActionCorrective.date_creation.desc()).all()
    return jsonify([{
        'id': a.id,
        'description': a.description,
        'statut': a.statut_label,
        'priorite': a.priorite,
        'date_echeance': a.date_echeance.isoformat() if a.date_echeance else None,
        'responsable': a.responsable.prenom + ' ' + a.responsable.nom if a.responsable else None,
        'source_type': a.source_type,
        'date_creation': a.date_creation.isoformat() if a.date_creation else None,
    } for a in actions])


@blueprint.route('/create', methods=['POST'])
@login_required
def create_action():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    action = ActionCorrective(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine,
        description=request.form.get('description'),
        type_action=request.form.get('type_action', 'corrective'),
        priorite=request.form.get('priorite', 'moyenne'),
        responsable_id=request.form.get('responsable_id', type=int),
        date_echeance=__import__('datetime').datetime.strptime(
            request.form['date_echeance'], '%Y-%m-%d').date()
        if request.form.get('date_echeance') else None,
        source_type=request.form.get('source_type'),
        source_id=request.form.get('source_id', type=int),
    )
    db.session.add(action)
    db.session.commit()
    flash('Action creee avec succes.', 'success')
    return redirect(url_for('actions.liste_actions'))


@blueprint.route('/<int:action_id>', methods=['GET', 'POST'])
@login_required
def detail_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    if request.method == 'POST':
        action.description = request.form.get('description', action.description)
        action.statut = request.form.get('statut', action.statut)
        action.priorite = request.form.get('priorite', action.priorite)
        action.responsable_id = request.form.get('responsable_id', type=int) or action.responsable_id
        if request.form.get('date_echeance'):
            action.date_echeance = __import__('datetime').datetime.strptime(
                request.form['date_echeance'], '%Y-%m-%d').date()
        action.efficacite = request.form.get('efficacite', type=float) or action.efficacite
        action.commentaire_efficacite = request.form.get('commentaire_efficacite')
        action.critere_efficacite = request.form.get('critere_efficacite')
        action.cause_identifiee = request.form.get('cause_identifiee')
        action.rca_pourquoi1 = request.form.get('rca_pourquoi1')
        action.rca_pourquoi2 = request.form.get('rca_pourquoi2')
        action.rca_pourquoi3 = request.form.get('rca_pourquoi3')
        action.rca_pourquoi4 = request.form.get('rca_pourquoi4')
        action.rca_pourquoi5 = request.form.get('rca_pourquoi5')
        action.rca_conclusion = request.form.get('rca_conclusion')
        db.session.commit()
        flash('Action mise a jour.', 'success')
        return redirect(url_for('actions.detail_action', action_id=action.id))

    return render_template('actions/detail.html', action=action)


@blueprint.route('/<int:action_id>/status', methods=['POST'])
@login_required
def update_status(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    new_status = request.json.get('statut') if request.is_json else request.form.get('statut')
    if new_status:
        action.statut = new_status
        if new_status == 'REALISE':
            action.date_realisation = __import__('datetime').datetime.utcnow().date()
        db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'statut': action.statut_label})
    flash('Statut mis a jour.', 'success')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.route('/<int:action_id>/proof/attach', methods=['POST'])
@login_required
def attach_proof(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    proof_id = request.json.get('proof_id') if request.is_json else request.form.get('proof_id')
    if proof_id:
        ref = ProofService.attach_proof(
            entreprise_id=current_user.entreprise_id,
            entity_type='action_corrective',
            entity_id=action.id,
            proof_id=int(proof_id),
            attached_by=current_user.id,
        )
        db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'reference_id': ref.id if ref else None})
    flash('Preuve attachee.', 'success')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.route('/<int:action_id>/proof/detach/<int:ref_id>', methods=['POST'])
@login_required
def detach_proof(action_id, ref_id):
    ref = tenant_get_or_404(ProofReference, ref_id)
    ProofService.detach_proof(ref.proof_master_id, ref.entity_type, ref.entity_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/<int:action_id>/delete', methods=['POST'])
@login_required
def delete_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    db.session.delete(action)
    db.session.commit()
    flash('Action supprimee.', 'success')
    return redirect(url_for('actions.liste_actions'))
