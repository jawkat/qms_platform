from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import EvaluationArticle, EntrepriseTexte, ConformiteEnum, Article, TexteVersion, TexteReglementaire
from app.conformite import blueprint
from app.utils.permissions import has_permission
from datetime import datetime, date
from sqlalchemy import or_


@blueprint.route('/')
@blueprint.route('/index')
@login_required
@has_permission('conformite.voir')
def index():
    textes = EntrepriseTexte.query.all()

    textes_data = []
    for et in textes:
        total_articles = Article.query.filter_by(texte_version_id=et.texte_version_id).count()
        evaluated = [e for e in et.evaluations if e.conforme is not None]
        eval_count = len(evaluated)
        conformes = sum(1 for e in evaluated if e.conforme == ConformiteEnum.CONFORME)
        non_conformes = sum(1 for e in evaluated if e.conforme == ConformiteEnum.NON_CONFORME)

        if total_articles == 0:
            progress_pct = 0
        else:
            progress_pct = round(eval_count / total_articles * 100)

        if eval_count == 0:
            prog_statut = 'non_commence'
        elif eval_count < total_articles:
            prog_statut = 'partiel'
        else:
            prog_statut = 'complete'

        textes_data.append({
            'et': et,
            'total_articles': total_articles,
            'eval_count': eval_count,
            'conformes': conformes,
            'non_conformes': non_conformes,
            'progress_pct': progress_pct,
            'prog_statut': prog_statut,
        })

    statut_filter = request.args.get('statut_evaluation')
    oblig_filter = request.args.get('statut_obligation')
    search = request.args.get('search')

    if statut_filter:
        textes_data = [d for d in textes_data if d['et'].statut_evaluation == statut_filter]
    if oblig_filter:
        textes_data = [d for d in textes_data if d['et'].statut_obligation == oblig_filter]
    if search:
        textes_data = [
            d for d in textes_data
            if d['et'].version and d['et'].version.texte
            and search.lower() in (d['et'].version.texte.titre or '').lower()
        ]

    return render_template('conformite/index.html', textes_data=textes_data)


@blueprint.route('/attribuer', methods=['POST'])
@login_required
@has_permission('conformite.modifier')
def attribuer():
    texte_version_id = request.form.get('texte_version_id', type=int)
    responsable_id = request.form.get('responsable_id', type=int)
    mode_evaluation = request.form.get('mode_evaluation', 'manuel')

    if not texte_version_id:
        flash('Veuillez sélectionner un texte.', 'danger')
        return redirect(url_for('conformite.index'))

    existing = EntrepriseTexte.query.filter_by(
        texte_version_id=texte_version_id
    ).first()
    if existing:
        flash('Ce texte est déjà attribué à votre entreprise.', 'warning')
        return redirect(url_for('conformite.index'))

    et = EntrepriseTexte(
        entreprise_id=current_user.entreprise_id,
        texte_version_id=texte_version_id,
        date_attribution=date.today(),
        statut_evaluation='non_commence',
        mode_evaluation=mode_evaluation,
        responsable_id=responsable_id or current_user.id,
    )
    db.session.add(et)
    db.session.commit()
    flash('Texte attribué avec succès.', 'success')
    return redirect(url_for('conformite.index'))


@blueprint.route('/<int:id>/update', methods=['POST'])
@login_required
@has_permission('conformite.modifier')
def update(id):
    et = EntrepriseTexte.query.filter_by(id=id).first_or_404()
    if 'statut_evaluation' in request.form:
        et.statut_evaluation = request.form['statut_evaluation']
    if 'score_conformite' in request.form:
        et.score_conformite = request.form.get('score_conformite', type=float)
    if 'statut_obligation' in request.form:
        et.statut_obligation = request.form['statut_obligation']
    et.derniere_mise_a_jour = datetime.utcnow()
    db.session.commit()
    flash('Mise à jour effectuée.', 'success')
    return jsonify({'success': True})


@blueprint.route('/<int:id>/delete', methods=['POST'])
@login_required
@has_permission('conformite.modifier')
def delete(id):
    et = EntrepriseTexte.query.filter_by(id=id).first_or_404()
    db.session.delete(et)
    db.session.commit()
    flash('Texte retiré de la liste.', 'success')
    return redirect(url_for('conformite.index'))


@blueprint.route('/api/liste')
@login_required
@has_permission('conformite.voir')
def api_liste():
    textes = EntrepriseTexte.query.all()
    data = []
    for et in textes:
        total_articles = Article.query.filter_by(texte_version_id=et.texte_version_id).count()
        evaluated = [e for e in et.evaluations if e.conforme is not None]
        eval_count = len(evaluated)
        conformes = sum(1 for e in evaluated if e.conforme == ConformiteEnum.CONFORME)
        non_conformes = sum(1 for e in evaluated if e.conforme == ConformiteEnum.NON_CONFORME)

        data.append({
            'id': et.id,
            'entreprise_id': et.entreprise_id,
            'texte_version_id': et.texte_version_id,
            'date_attribution': et.date_attribution.isoformat() if et.date_attribution else None,
            'score_conformite': et.score_conformite,
            'statut_evaluation': et.statut_evaluation,
            'statut_obligation': et.statut_obligation,
            'mode_evaluation': et.mode_evaluation,
            'derniere_mise_a_jour': et.derniere_mise_a_jour.isoformat() if et.derniere_mise_a_jour else None,
            'responsable_id': et.responsable_id,
            'total_articles': total_articles,
            'eval_count': eval_count,
            'conformes': conformes,
            'non_conformes': non_conformes,
            'titre': et.version.texte.titre if et.version and et.version.texte else '',
            'code': et.version.texte.code if et.version and et.version.texte else '',
            'version_numero': et.version.numero_version if et.version else '',
        })
    return jsonify(data)


@blueprint.route('/search')
@login_required
@has_permission('conformite.voir')
def search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        like = f'%{query}%'
        articles = Article.query.filter(
            db.or_(Article.contenu.ilike(like), Article.resume_article.ilike(like))
        ).order_by(Article.numero_article).limit(100).all()

        for article in articles:
            version = TexteVersion.query.get(article.texte_version_id)
            texte = TexteReglementaire.query.get(version.texte_id) if version else None
            evaluation = None
            if texte:
                et = EntrepriseTexte.query.filter_by(
                    texte_version_id=version.id
                ).first()
                if et:
                    evaluation = EvaluationArticle.query.filter_by(
                        entreprise_texte_id=et.id, article_id=article.id
                    ).first()
            results.append({
                'article': article,
                'version': version,
                'texte': texte,
                'evaluation': evaluation,
            })

    return render_template('conformite/search_results.html', results=results, query=query)
