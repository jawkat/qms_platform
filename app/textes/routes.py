from datetime import datetime, date, timedelta

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Domaine, TexteReglementaire, TexteVersion, Article, ExigenceType, NiveauRisqueType, Secteur, EntrepriseTexte, EvaluationArticle, ConformiteEnum
from app.textes import textes
from app.utils.permissions import has_permission
from sqlalchemy import func


@textes.route('/')
@login_required
def index():
    query = TexteReglementaire.query

    domaine_id = request.args.get('domaine', type=int)
    type_filter = request.args.get('type')
    search = request.args.get('search')

    if domaine_id:
        query = query.filter(TexteReglementaire.domaine_id == domaine_id)
    if type_filter:
        query = query.filter(TexteReglementaire.type == type_filter)
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                TexteReglementaire.titre.ilike(like),
                TexteReglementaire.code.ilike(like),
                TexteReglementaire.description.ilike(like),
            )
        )

    textes_list = query.order_by(TexteReglementaire.code).all()
    domaines = Domaine.query.order_by(Domaine.nom).all()
    types = [r[0] for r in db.session.query(TexteReglementaire.type).distinct().filter(TexteReglementaire.type.isnot(None)).order_by(TexteReglementaire.type).all()]

    filters = {}
    if domaine_id:
        filters['domaine'] = domaine_id
    if type_filter:
        filters['type'] = type_filter
    if search:
        filters['search'] = search

    return render_template('textes/index.html', textes=textes_list, domaines=domaines, types=types, filters=filters)


@textes.route('/<int:texte_id>')
@login_required
def detail(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    versions = TexteVersion.query.filter_by(texte_id=texte_id).order_by(TexteVersion.numero_version.desc()).all()
    articles = []
    if texte.version_active_id:
        articles = Article.query.filter_by(texte_version_id=texte.version_active_id).order_by(Article.numero_article).all()
    return render_template('textes/detail.html', texte=texte, versions=versions, articles=articles)


@textes.route('/version/<int:version_id>')
@login_required
def version_detail(version_id):
    version = TexteVersion.query.get_or_404(version_id)
    articles = Article.query.filter_by(texte_version_id=version_id).order_by(Article.numero_article).all()
    return render_template('textes/version_detail.html', version=version, articles=articles)


@textes.route('/api/liste')
@login_required
def api_liste():
    textes_list = TexteReglementaire.query.order_by(TexteReglementaire.code).all()
    data = []
    for t in textes_list:
        data.append({
            'id': t.id,
            'code': t.code,
            'titre': t.titre,
            'type': t.type,
            'domaine': t.domaine,
            'domaine_id': t.domaine_id,
            'sousdomaine': t.sousdomaine,
            'theme': t.theme,
            'referentiel': t.referentiel,
            'version_active_id': t.version_active_id,
            'date_creation': t.date_creation.isoformat() if t.date_creation else None,
        })
    return jsonify(data)


@textes.route('/api/domaines')
@login_required
def api_domaines():
    domaines = Domaine.query.order_by(Domaine.nom).all()
    data = [{'id': d.id, 'nom': d.nom, 'description': d.description} for d in domaines]
    return jsonify(data)


# --- Admin CRUD API routes ---

@textes.route('/api/<int:texte_id>')
@login_required
def api_texte(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    versions = TexteVersion.query.filter_by(texte_id=texte_id).order_by(TexteVersion.numero_version.desc()).all()
    return jsonify({
        'id': texte.id,
        'code': texte.code,
        'titre': texte.titre,
        'description': texte.description,
        'type': texte.type,
        'domaine': texte.domaine,
        'domaine_id': texte.domaine_id,
        'sousdomaine': texte.sousdomaine,
        'theme': texte.theme,
        'referentiel': texte.referentiel,
        'version_active_id': texte.version_active_id,
        'versions': [{
            'id': v.id,
            'numero_version': v.numero_version,
            'date_publication': v.date_publication.isoformat() if v.date_publication else None,
            'preambule': v.preambule,
            'statut': v.statut,
        } for v in versions],
        'date_creation': texte.date_creation.isoformat() if texte.date_creation else None,
    })


@textes.route('/api/create', methods=['POST'])
@login_required
def api_create():
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    if not data.get('code') or not data.get('titre'):
        return jsonify({'error': 'code et titre sont requis'}), 400
    texte = TexteReglementaire(
        code=data['code'],
        titre=data['titre'],
        description=data.get('description'),
        type=data.get('type'),
        domaine=data.get('domaine'),
        domaine_id=data.get('domaine_id'),
        referentiel=data.get('referentiel'),
    )
    db.session.add(texte)
    db.session.commit()
    return jsonify({'success': True, 'id': texte.id}), 201


@textes.route('/api/<int:texte_id>/update', methods=['POST'])
@login_required
def api_update(texte_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    texte = TexteReglementaire.query.get_or_404(texte_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    for field in ('code', 'titre', 'description', 'type', 'domaine', 'domaine_id', 'referentiel'):
        if field in data:
            setattr(texte, field, data[field])
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/api/<int:texte_id>/delete', methods=['POST'])
@login_required
def api_delete(texte_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    texte = TexteReglementaire.query.get_or_404(texte_id)
    TexteVersion.query.filter_by(texte_id=texte_id).delete()
    db.session.delete(texte)
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/api/<int:texte_id>/version/create', methods=['POST'])
@login_required
def api_version_create(texte_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    TexteReglementaire.query.get_or_404(texte_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    version = TexteVersion(
        texte_id=texte_id,
        numero_version=data.get('numero_version'),
        date_publication=datetime.strptime(data['date_publication'], '%Y-%m-%d').date() if data.get('date_publication') else None,
        preambule=data.get('preambule'),
    )
    db.session.add(version)
    db.session.commit()
    return jsonify({'success': True, 'id': version.id}), 201


@textes.route('/api/version/<int:version_id>/update', methods=['POST'])
@login_required
def api_version_update(version_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    version = TexteVersion.query.get_or_404(version_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    if 'numero_version' in data:
        version.numero_version = data['numero_version']
    if 'date_publication' in data and data['date_publication']:
        version.date_publication = datetime.strptime(data['date_publication'], '%Y-%m-%d').date()
    if 'preambule' in data:
        version.preambule = data['preambule']
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/api/version/<int:version_id>/delete', methods=['POST'])
@login_required
def api_version_delete(version_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    version = TexteVersion.query.get_or_404(version_id)
    if Article.query.filter_by(texte_version_id=version_id).first():
        return jsonify({'error': 'Impossible de supprimer une version qui contient des articles'}), 400
    db.session.delete(version)
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/api/version/<int:version_id>/article/create', methods=['POST'])
@login_required
def api_article_create(version_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    TexteVersion.query.get_or_404(version_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    exigence = ExigenceType[data['exigence_type']] if data.get('exigence_type') else ExigenceType.INFORMATION
    risque = NiveauRisqueType[data['niveau_risque']] if data.get('niveau_risque') else NiveauRisqueType.FAIBLE
    article = Article(
        texte_version_id=version_id,
        numero_article=data.get('numero_article'),
        contenu=data.get('contenu'),
        exigence_type=exigence,
        niveau_risque=risque,
        resume_article=data.get('resume_article'),
        acteur=data.get('acteur'),
    )
    db.session.add(article)
    db.session.commit()
    return jsonify({'success': True, 'id': article.id}), 201


@textes.route('/api/article/<int:article_id>/update', methods=['POST'])
@login_required
def api_article_update(article_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    article = Article.query.get_or_404(article_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    for field in ('numero_article', 'contenu', 'resume_article', 'explication_detaillee', 'preuve_conformite', 'acteur'):
        if field in data:
            setattr(article, field, data[field])
    if 'exigence_type' in data:
        article.exigence_type = ExigenceType[data['exigence_type']]
    if 'niveau_risque' in data:
        article.niveau_risque = NiveauRisqueType[data['niveau_risque']]
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/api/article/<int:article_id>/delete', methods=['POST'])
@login_required
def api_article_delete(article_id):
    if not current_user.has_permission('textes.modifier'):
        return jsonify({'error': 'Permission refusée'}), 403
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Admin UI form routes (HTML, not JSON)
# ---------------------------------------------------------------------------


@textes.route('/create', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def create_texte():
    if request.method == 'POST':
        texte = TexteReglementaire(
            code=request.form.get('code', '').strip(),
            titre=request.form.get('titre', '').strip(),
            description=request.form.get('description', '').strip(),
            type=request.form.get('type'),
            domaine=request.form.get('domaine'),
            domaine_id=request.form.get('domaine_id', type=int),
            sousdomaine=request.form.get('sousdomaine'),
            theme=request.form.get('theme'),
            referentiel=request.form.get('referentiel'),
        )
        db.session.add(texte)
        db.session.flush()
        secteur_ids = request.form.getlist('secteurs')
        if secteur_ids:
            secteurs = Secteur.query.filter(Secteur.id.in_([int(s) for s in secteur_ids if s])).all()
            texte.secteurs.extend(secteurs)
        db.session.commit()
        flash('Texte réglementaire créé avec succès.', 'success')
        return redirect(url_for('textes.detail', texte_id=texte.id))

    domaines = Domaine.query.order_by(Domaine.nom).all()
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('textes/texte_form.html', texte=None, domaines=domaines, secteurs=secteurs)


@textes.route('/<int:texte_id>/edit', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def edit_texte(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    if request.method == 'POST':
        texte.code = request.form.get('code', '').strip()
        texte.titre = request.form.get('titre', '').strip()
        texte.description = request.form.get('description', '').strip()
        texte.type = request.form.get('type')
        texte.domaine = request.form.get('domaine')
        texte.domaine_id = request.form.get('domaine_id', type=int)
        texte.sousdomaine = request.form.get('sousdomaine')
        texte.theme = request.form.get('theme')
        texte.referentiel = request.form.get('referentiel')
        secteur_ids = [int(s) for s in request.form.getlist('secteurs') if s]
        texte.secteurs = Secteur.query.filter(Secteur.id.in_(secteur_ids)).all() if secteur_ids else []
        db.session.commit()
        flash('Texte réglementaire modifié avec succès.', 'success')
        return redirect(url_for('textes.detail', texte_id=texte.id))

    domaines = Domaine.query.order_by(Domaine.nom).all()
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('textes/texte_form.html', texte=texte, domaines=domaines, secteurs=secteurs)


@textes.route('/<int:texte_id>/delete', methods=['POST'])
@login_required
@has_permission('textes.modifier')
def delete_texte(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    TexteVersion.query.filter_by(texte_id=texte_id).delete()
    db.session.delete(texte)
    db.session.commit()
    flash('Texte réglementaire supprimé.', 'success')
    return redirect(url_for('textes.index'))


@textes.route('/<int:texte_id>/version/create', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def create_version(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    if request.method == 'POST':
        version = TexteVersion(
            texte_id=texte_id,
            numero_version=request.form.get('numero_version'),
            date_publication=(
                datetime.strptime(request.form['date_publication'], '%Y-%m-%d').date()
                if request.form.get('date_publication') else None
            ),
            preambule=request.form.get('preambule'),
            commentaire_version=request.form.get('commentaire_version'),
            statut=request.form.get('statut', 'projet'),
            cree_par=current_user.id,
            version_precedente_id=request.form.get('version_precedente_id', type=int) or None,
        )
        db.session.add(version)
        db.session.commit()
        if request.form.get('set_active'):
            texte.version_active_id = version.id
            db.session.commit()
        flash('Version créée avec succès.', 'success')
        return redirect(url_for('textes.detail', texte_id=texte_id))

    versions = TexteVersion.query.filter_by(texte_id=texte_id).order_by(TexteVersion.numero_version.desc()).all()
    return render_template('textes/version_form.html', version=None, texte=texte, versions=versions)


@textes.route('/version/<int:version_id>/edit', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def edit_version(version_id):
    version = TexteVersion.query.get_or_404(version_id)
    if request.method == 'POST':
        version.numero_version = request.form.get('numero_version')
        version.date_publication = (
            datetime.strptime(request.form['date_publication'], '%Y-%m-%d').date()
            if request.form.get('date_publication') else None
        )
        version.preambule = request.form.get('preambule')
        version.commentaire_version = request.form.get('commentaire_version')
        version.statut = request.form.get('statut', 'projet')
        db.session.commit()
        if request.form.get('set_active'):
            version.texte.version_active_id = version.id
            db.session.commit()
        flash('Version modifiée avec succès.', 'success')
        return redirect(url_for('textes.version_detail', version_id=version.id))

    texte = version.texte
    versions = TexteVersion.query.filter(
        TexteVersion.texte_id == texte.id, TexteVersion.id != version.id
    ).order_by(TexteVersion.numero_version.desc()).all()
    return render_template('textes/version_form.html', version=version, texte=texte, versions=versions)


@textes.route('/version/<int:version_id>/delete', methods=['POST'])
@login_required
@has_permission('textes.modifier')
def delete_version(version_id):
    version = TexteVersion.query.get_or_404(version_id)
    texte_id = version.texte_id
    if Article.query.filter_by(texte_version_id=version_id).first():
        flash('Impossible de supprimer une version qui contient des articles.', 'danger')
        return redirect(url_for('textes.version_detail', version_id=version_id))
    db.session.delete(version)
    db.session.commit()
    flash('Version supprimée.', 'success')
    return redirect(url_for('textes.detail', texte_id=texte_id))


@textes.route('/version/<int:version_id>/article/create', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def create_article(version_id):
    version = TexteVersion.query.get_or_404(version_id)
    if request.method == 'POST':
        exigence = ExigenceType[request.form['exigence_type']] if request.form.get('exigence_type') else ExigenceType.INFORMATION
        risque = NiveauRisqueType[request.form['niveau_risque']] if request.form.get('niveau_risque') else NiveauRisqueType.FAIBLE
        article = Article(
            texte_version_id=version_id,
            numero_article=request.form.get('numero_article', type=int),
            contenu=request.form.get('contenu'),
            exigence_type=exigence,
            niveau_risque=risque,
            resume_article=request.form.get('resume_article'),
            explication_detaillee=request.form.get('explication_detaillee'),
            preuve_conformite=request.form.get('preuve_conformite'),
            acteur=request.form.get('acteur'),
        )
        db.session.add(article)
        db.session.commit()
        flash('Article créé avec succès.', 'success')
        return redirect(url_for('textes.version_detail', version_id=version_id))

    return render_template('textes/article_form.html', article=None, version=version)


@textes.route('/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@has_permission('textes.modifier')
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        article.numero_article = request.form.get('numero_article', type=int)
        article.contenu = request.form.get('contenu')
        article.resume_article = request.form.get('resume_article')
        article.explication_detaillee = request.form.get('explication_detaillee')
        article.preuve_conformite = request.form.get('preuve_conformite')
        article.acteur = request.form.get('acteur')
        if request.form.get('exigence_type'):
            article.exigence_type = ExigenceType[request.form['exigence_type']]
        if request.form.get('niveau_risque'):
            article.niveau_risque = NiveauRisqueType[request.form['niveau_risque']]
        db.session.commit()
        flash('Article modifié avec succès.', 'success')
        return redirect(url_for('textes.version_detail', version_id=article.texte_version_id))

    return render_template('textes/article_form.html', article=article, version=article.version)


@textes.route('/article/<int:article_id>/delete', methods=['POST'])
@login_required
@has_permission('textes.modifier')
def delete_article(article_id):
    article = Article.query.get_or_404(article_id)
    version_id = article.texte_version_id
    db.session.delete(article)
    db.session.commit()
    flash('Article supprimé.', 'success')
    return redirect(url_for('textes.version_detail', version_id=version_id))


# ---------------------------------------------------------------------------
# Bibliothèque HSE (user-facing)
# ---------------------------------------------------------------------------

NEW_DAYS = 30


def _compute_library_linkage(entreprise_id, texte_id, version_active_id):
    """Return link state for a texte for the given enterprise."""
    if not version_active_id or not entreprise_id:
        return 'unlinked'
    et = EntrepriseTexte.query.filter_by(
        entreprise_id=entreprise_id, texte_version_id=version_active_id
    ).first()
    if not et:
        return 'unlinked'
    eval_count = EvaluationArticle.query.filter_by(entreprise_texte_id=et.id).count()
    eval_done = EvaluationArticle.query.filter(
        EvaluationArticle.entreprise_texte_id == et.id,
        EvaluationArticle.date_evaluation.isnot(None)
    ).count()
    if eval_done > 0:
        return 'evaluated'
    return 'linked'


def _render_library(tab, filters):
    eid = current_user.entreprise_id
    query = TexteReglementaire.query

    q = filters.get('q', '').strip()
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                TexteReglementaire.code.ilike(like),
                TexteReglementaire.titre.ilike(like),
                TexteReglementaire.description.ilike(like),
            )
        )

    domaine_id = filters.get('domaine_id')
    if domaine_id:
        query = query.filter(TexteReglementaire.domaine_id == domaine_id)

    referentiel = filters.get('referentiel')
    if referentiel:
        query = query.filter(TexteReglementaire.referentiel == referentiel)

    secteur_ids = filters.get('secteur_ids', [])
    if secteur_ids:
        query = query.filter(TexteReglementaire.secteurs.any(Secteur.id.in_(secteur_ids)))

    sort = filters.get('sort', 'updated')
    if sort == 'code':
        query = query.order_by(TexteReglementaire.code)
    elif sort == 'title':
        query = query.order_by(TexteReglementaire.titre)
    elif sort == 'domain':
        query = query.order_by(TexteReglementaire.domaine)
    else:
        query = query.order_by(TexteReglementaire.date_creation.desc())

    all_textes = query.all()
    total = len(all_textes)

    now = date.today()
    cutoff = now - timedelta(days=NEW_DAYS)

    # Compute counts per status filter
    counts = {'all': total, 'linked': 0, 'unlinked': 0, 'to_evaluate': 0, 'evaluated': 0}
    enriched = []
    for t in all_textes:
        v = t.version_active
        is_new = t.date_creation and t.date_creation.date() >= cutoff if t.date_creation else False
        has_update = v and v.date_publication and v.date_publication >= cutoff if v and v.date_publication else False
        link_state = _compute_library_linkage(eid, t.id, v.id if v else None)
        entreprise_count = EntrepriseTexte.query.filter_by(texte_version_id=v.id).count() if v else 0

        if link_state in ('linked', 'evaluated'):
            counts['linked'] += 1
        else:
            counts['unlinked'] += 1
        if link_state == 'linked':
            counts['to_evaluate'] += 1
        if link_state == 'evaluated':
            counts['evaluated'] += 1

        enriched.append({
            'texte': t,
            'version_active': v,
            'is_new': is_new,
            'has_update': has_update,
            'link_state': link_state,
            'entreprise_count': entreprise_count,
        })

    status_filter = filters.get('status', 'all')
    if status_filter == 'linked':
        enriched = [i for i in enriched if i['link_state'] in ('linked', 'evaluated')]
    elif status_filter == 'unlinked':
        enriched = [i for i in enriched if i['link_state'] == 'unlinked']
    elif status_filter == 'to_evaluate':
        enriched = [i for i in enriched if i['link_state'] == 'linked']
    elif status_filter == 'evaluated':
        enriched = [i for i in enriched if i['link_state'] == 'evaluated']

    # Pagination
    per_page = filters.get('per_page', 20)
    page = filters.get('page', 1)
    total_filtered = len(enriched)
    pages = max(1, (total_filtered + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    enriched_page = enriched[start:end]

    domaines = Domaine.query.order_by(Domaine.nom).all()
    referentiels = db.session.query(TexteReglementaire.referentiel).distinct().all()
    referentiels = sorted([r[0] for r in referentiels if r[0]])
    secteurs = Secteur.query.order_by(Secteur.nom).all()

    return render_template(
        'textes/library.html',
        tab=tab,
        textes=enriched_page,
        total_textes=total,
        counts=counts,
        filters=filters,
        domaines=domaines,
        referentiels=referentiels,
        secteurs=secteurs,
        per_page=per_page,
        pagination={'page': page, 'pages': pages, 'total': total_filtered},
    )


@textes.route('/bibliotheque')
@textes.route('/bibliotheque/tous-les-textes')
@login_required
def library_all():
    filters = _parse_library_filters()
    filters['status'] = request.args.get('status', 'all')
    return _render_library('all', filters)


@textes.route('/bibliotheque/nouveaux-textes')
@login_required
def library_new():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('new', filters)


@textes.route('/bibliotheque/mises-a-jour-recentes')
@login_required
def library_recent():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('recent', filters)


def _parse_library_filters():
    secteur_ids = request.args.getlist('secteur', type=int)
    return {
        'q': request.args.get('q', ''),
        'domaine_id': request.args.get('domaine_id', type=int),
        'referentiel': request.args.get('referentiel', ''),
        'secteur_ids': secteur_ids,
        'sort': request.args.get('sort', 'updated'),
        'order': request.args.get('order', 'desc'),
        'per_page': request.args.get('per_page', 20, type=int),
        'page': request.args.get('page', 1, type=int),
    }
