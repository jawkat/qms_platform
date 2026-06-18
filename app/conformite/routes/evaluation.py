from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import EvaluationArticle, EntrepriseTexte, ActionCorrective, Utilisateur, ProofReference, Article
from app.conformite import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import has_permission
from app.services.proof_service import ProofService
from datetime import datetime


@blueprint.route('/evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
@login_required
@has_permission('conformite.voir')
def evaluation_detail(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    responsables = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id).all()

    if request.method == 'POST':
        if request.form.get('conforme') is not None:
            evaluation.conforme = request.form.get('conforme', evaluation.conforme)
        if request.form.get('applicable') is not None:
            evaluation.applicable = request.form.get('applicable', evaluation.applicable)
        evaluation.observation = request.form.get('observation', evaluation.observation)
        evaluation.date_evaluation = datetime.utcnow()
        evaluation.evalue_par = current_user.id
        db.session.commit()

        nav = request.form.get('nav')
        if nav == 'save_next' or nav == 'save_prev':
            all_evals = EvaluationArticle.query.filter_by(
                entreprise_texte_id=evaluation.entreprise_texte_id
            ).join(Article, EvaluationArticle.article_id == Article.id).order_by(Article.numero_article).all()
            idx = next((i for i, e in enumerate(all_evals) if e.id == evaluation_id), -1)
            if nav == 'save_next' and idx < len(all_evals) - 1:
                return redirect(url_for('conformite.evaluation_detail', evaluation_id=all_evals[idx + 1].id))
            elif nav == 'save_prev' and idx > 0:
                return redirect(url_for('conformite.evaluation_detail', evaluation_id=all_evals[idx - 1].id))
        return redirect(url_for('conformite.evaluation_detail', evaluation_id=evaluation_id))

    all_evals = EvaluationArticle.query.filter_by(
        entreprise_texte_id=evaluation.entreprise_texte_id
    ).join(Article, EvaluationArticle.article_id == Article.id).order_by(Article.numero_article).all()

    current_idx = next((i for i, e in enumerate(all_evals) if e.id == evaluation_id), -1)
    prev_evaluation = all_evals[current_idx - 1] if current_idx > 0 else None
    next_evaluation = all_evals[current_idx + 1] if current_idx < len(all_evals) - 1 else None

    stats = {
        'total': len(all_evals),
        'current': current_idx + 1,
        'evalue': sum(1 for e in all_evals if e.date_evaluation is not None),
        'conforme': sum(1 for e in all_evals if e.conforme and e.conforme.name == 'CONFORME'),
        'non_conforme': sum(1 for e in all_evals if e.conforme and e.conforme.name == 'NON_CONFORME'),
        'non_applicable': sum(1 for e in all_evals if e.applicable and e.applicable.name == 'NON_APPLICABLE'),
    }

    return render_template(
        'conformite/evaluation_detail.html',
        evaluation=evaluation,
        all_evals=all_evals,
        current_idx=current_idx,
        prev_evaluation=prev_evaluation,
        next_evaluation=next_evaluation,
        stats=stats,
        responsables=responsables,
    )


@blueprint.route('/evaluation/<int:evaluation_id>/action/add', methods=['POST'])
@login_required
@has_permission('conformite.modifier')
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
@has_permission('conformite.voir')
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
@has_permission('conformite.modifier')
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


@blueprint.route('/evaluation/<int:evaluation_id>/proof/liste')
@login_required
@has_permission('conformite.voir')
def list_proofs(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    refs = ProofReference.query.filter_by(
        entity_type='evaluation_article', entity_id=evaluation.id
    ).all()
    return jsonify([{
        'id': r.id,
        'proof_id': r.proof_master_id,
        'nom_fichier': r.proof_master.nom_fichier if r.proof_master else '?',
        'date_attached': r.date_attached.isoformat() if r.date_attached else None,
    } for r in refs])
