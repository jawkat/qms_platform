from flask import render_template, request, jsonify, redirect, url_for
from flask_login import current_user
from app import db
from app.models import EvaluationArticle, EntrepriseTexte, ActionCorrective, Utilisateur, ProofReference, Article, TexteVersion, TexteReglementaire, ConformiteEnum
from app.conformite import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.services.proof_service import ProofService
from datetime import datetime, date
from sqlalchemy import or_


def _update_entreprise_texte_stats(entreprise_texte_id):
    et = EntrepriseTexte.query.get(entreprise_texte_id)
    if not et:
        return
    evals = EvaluationArticle.query.filter_by(entreprise_texte_id=et.id).all()
    total = Article.query.filter_by(texte_version_id=et.texte_version_id).count()
    evaluated = [e for e in evals if e.conforme is not None]
    conforms = sum(1 for e in evaluated if e.conforme == ConformiteEnum.CONFORME)
    non_conforms = sum(1 for e in evaluated if e.conforme == ConformiteEnum.NON_CONFORME)

    if total > 0 and len(evaluated) > 0:
        et.score_conformite = round(conforms / total * 100, 1)
    else:
        et.score_conformite = 0

    if len(evaluated) == 0:
        et.statut_evaluation = 'non_commence'
    elif len(evaluated) < total:
        et.statut_evaluation = 'en_cours'
    else:
        et.statut_evaluation = 'complete'

    et.derniere_mise_a_jour = datetime.utcnow()
    db.session.commit()


@blueprint.route('/evaluation/<int:evaluation_id>', methods=['GET', 'POST'])
@access_required(permission='conformite.voir')
def evaluation_detail(evaluation_id):
    evaluation = tenant_get_or_404(EvaluationArticle, evaluation_id)
    responsables = Utilisateur.query.all()

    if request.method == 'POST':
        if request.form.get('conforme'):
            evaluation.conforme = request.form.get('conforme')
        if request.form.get('applicable'):
            evaluation.applicable = request.form.get('applicable')
        evaluation.observation = request.form.get('observation', evaluation.observation)
        evaluation.date_evaluation = datetime.utcnow()
        evaluation.evalue_par = current_user.id
        db.session.commit()

        _update_entreprise_texte_stats(evaluation.entreprise_texte_id)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})

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
        'evalue': sum(1 for e in all_evals if e.conforme is not None),
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
@access_required(permission='conformite.modifier')
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
@access_required(permission='conformite.voir')
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
@access_required(permission='conformite.modifier')
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
@access_required(permission='conformite.voir')
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


# ---------------------------------------------------------------------------
# Non-conformités HSE
# ---------------------------------------------------------------------------

@blueprint.route('/nonconformites')
@access_required(permission='conformite.voir')
def nonconformites():
    q = EvaluationArticle.query.join(EntrepriseTexte)

    conforme_filter = request.args.get('conforme')
    if conforme_filter:
        q = q.filter(EvaluationArticle.conforme == ConformiteEnum[conforme_filter])
    else:
        q = q.filter(
            db.or_(
                EvaluationArticle.conforme == ConformiteEnum.NON_CONFORME,
                EvaluationArticle.conforme.is_(None))
        )

    texte_id = request.args.get('texte_id', type=int)
    if texte_id:
        q = q.join(Article).join(TexteVersion).filter(TexteVersion.texte_id == texte_id)

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.join(Article, EvaluationArticle.article_id == Article.id).filter(
            db.or_(
                Article.contenu.ilike(like),
                Article.resume_article.ilike(like),
                EvaluationArticle.observation.ilike(like))
        )

    q = q.order_by(EvaluationArticle.date_evaluation.desc().nullslast())
    all_evals = q.all()

    # Pagination
    per_page = request.args.get('per_page', 50, type=int)
    page = request.args.get('page', 1, type=int)
    total = len(all_evals)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    evals_page = all_evals[start:start + per_page]

    nonconformites_data = []
    for ev in evals_page:
        article = Article.query.get(ev.article_id)
        version = TexteVersion.query.get(article.texte_version_id) if article else None
        texte = TexteReglementaire.query.get(version.texte_id) if version else None
        nonconformites_data.append({
            'evaluation': ev,
            'article': article,
            'version': version,
            'texte_titre': texte.titre if texte else '',
        })

    entreprise_textes = EntrepriseTexte.query.all()

    filters = {
        'conforme': conforme_filter or '',
        'texte_id': texte_id or '',
        'q': search,
    }

    return render_template(
        'conformite/nonconformites.html',
        nonconformites=nonconformites_data,
        total=total,
        filters=filters,
        entreprise_textes=entreprise_textes,
        pagination={'page': page, 'pages': pages, 'total': total},
    )


@blueprint.route('/api/nonconformites')
@access_required(permission='conformite.voir')
def api_nonconformites():
    q = EvaluationArticle.query.join(EntrepriseTexte)

    conforme = request.args.get('conforme')
    if conforme:
        q = q.filter(EvaluationArticle.conforme == ConformiteEnum[conforme])

    texte_id = request.args.get('texte_id', type=int)
    if texte_id:
        q = q.join(Article).join(TexteVersion).filter(TexteVersion.texte_id == texte_id)

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.join(Article).filter(
            db.or_(Article.contenu.ilike(like), EvaluationArticle.observation.ilike(like))
        )

    q = q.order_by(EvaluationArticle.date_evaluation.desc().nullslast())
    evals = q.all()

    return jsonify([{
        'id': e.id,
        'article_id': e.article_id,
        'conforme': e.conforme.name if e.conforme else None,
        'observation': e.observation,
        'date_evaluation': e.date_evaluation.isoformat() if e.date_evaluation else None,
    } for e in evals])


# ---------------------------------------------------------------------------
# Preuves de conformité (proof management in conformite)
# ---------------------------------------------------------------------------

@blueprint.route('/preuves/gestion')
@access_required(permission='conformite.voir')
def preuves_gestion():
    from app.models import ProofMaster, ProofReference
    from datetime import date, timedelta

    proofs = ProofMaster.query.filter_by(
        statut='ACTIF'
    ).order_by(ProofMaster.date_creation.desc()).all()

    today = date.today()
    preuves = []
    for p in proofs:
        refs_count = ProofReference.query.filter_by(proof_master_id=p.id).count()
        etat = 'valide'
        if p.validite:
            if p.validite < today:
                etat = 'expire'
            elif (p.validite - today).days <= 30:
                etat = 'expire_bientot'
        preuves.append({'proof': p, 'refs_count': refs_count, 'etat': etat})

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        preuves = [i for i in preuves if like.lower() in (i['proof'].nom_fichier or '').lower()
                   or like.lower() in (i['proof'].description or '').lower()]

    statut_filter = request.args.get('statut')
    if statut_filter:
        preuves = [i for i in preuves if i['etat'] == statut_filter]

    return render_template(
        'conformite/preuves_alertes_centre.html',
        preuves=preuves,
        filters={'q': search, 'statut': statut_filter or ''},
    )


@blueprint.route('/preuves/<int:proof_id>/mettre_a_jour', methods=['POST'])
@access_required(permission='documents.upload')
def preuve_mettre_a_jour(proof_id):
    from app.models import ProofMaster
    proof = tenant_get_or_404(ProofMaster, proof_id)
    proof.description = request.form.get('description', proof.description)
    if request.form.get('validite'):
        try:
            proof.validite = datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    proof.categorie = request.form.get('categorie', proof.categorie)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/preuves/<int:proof_id>/archiver', methods=['POST'])
@access_required(permission='documents.archiver')
def preuve_archiver(proof_id):
    ProofService.archive_proof(proof_id)
    db.session.commit()
    flash('Preuve archivée.', 'success')
    return redirect(url_for('conformite.preuves_gestion'))


@blueprint.route('/preuves/<int:proof_id>/supprimer', methods=['POST'])
@access_required(permission='documents.archiver')
def preuve_supprimer(proof_id):
    ProofService.hard_delete_proof(proof_id)
    db.session.commit()
    flash('Preuve supprimée.', 'success')
    return redirect(url_for('conformite.preuves_gestion'))


@blueprint.route('/evaluation/<int:evaluation_id>/proof/<int:proof_id>/detach', methods=['POST'])
@access_required(permission='conformite.modifier')
def detach_proof(evaluation_id, proof_id):
    tenant_get_or_404(EvaluationArticle, evaluation_id)
    ref = ProofService.detach_proof(proof_id, 'evaluation_article', evaluation_id)
    db.session.commit()
    return jsonify({'success': True, 'detached': ref is not None})
