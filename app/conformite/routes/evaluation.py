from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import EvaluationArticle, EntrepriseTexte, ActionCorrective
from app.conformite import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.services.proof_service import ProofService
from datetime import datetime


@blueprint.route('/evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
@login_required
def evaluation_detail(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    if request.method == 'POST':
        evaluation.conforme = request.form.get('conforme', evaluation.conforme)
        evaluation.applicable = request.form.get('applicable', evaluation.applicable)
        evaluation.observation = request.form.get('observation', evaluation.observation)
        evaluation.date_evaluation = datetime.utcnow()
        evaluation.evalue_par = current_user.id
        db.session.commit()
        return jsonify({'success': True})
    return render_template('conformite/evaluation_detail.html', evaluation=evaluation)


@blueprint.route('/evaluation/<int:evaluation_id>/action/add', methods=['POST'])
@login_required
def add_action(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    action = ActionCorrective(
        entreprise_id=current_user.entreprise_id,
        domaine='hse',
        description=request.form.get('description'),
        source_type='evaluation_article',
        source_id=evaluation.id,
        type_action=request.form.get('type_action', 'corrective'),
        priorite=request.form.get('priorite', 'moyenne'),
        responsable_id=request.form.get('responsable_id', type=int),
        date_echeance=datetime.strptime(request.form['date_echeance'], '%Y-%m-%d').date()
        if request.form.get('date_echeance') else None,
    )
    db.session.add(action)
    db.session.commit()
    return jsonify({'success': True, 'action_id': action.id})


@blueprint.route('/evaluation/<int:evaluation_id>/actions')
@login_required
def list_actions(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    actions = ActionCorrective.query.filter_by(
        source_type='evaluation_article', source_id=evaluation.id
    ).all()
    return jsonify([{
        'id': a.id,
        'description': a.description,
        'statut': a.statut_label,
        'priorite': a.priorite,
        'date_echeance': a.date_echeance.isoformat() if a.date_echeance else None,
    } for a in actions])


@blueprint.route('/evaluation/<int:evaluation_id>/proof/attach', methods=['POST'])
@login_required
def attach_proof(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    proof_id = request.json.get('proof_id') if request.is_json else request.form.get('proof_id')
    if proof_id:
        ref = ProofService.attach_proof(
            entreprise_id=current_user.entreprise_id,
            entity_type='evaluation_article',
            entity_id=evaluation.id,
            proof_id=int(proof_id),
            attached_by=current_user.id,
        )
        db.session.commit()
    return jsonify({'success': True})
