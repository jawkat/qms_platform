from datetime import date, timedelta
from flask import render_template, request, redirect, url_for, jsonify, current_app
from flask_login import current_user
from app.utils.permissions import access_required
from app import db
from app.models import Domaine, TexteReglementaire, TexteVersion, Article, Secteur, EntrepriseTexte, EvaluationArticle, ActionCorrective, ConformiteEnum, Utilisateur
from app.textes import textes

NEW_DAYS = 30


def _compute_library_linkage(entreprise_id, texte_id, version_active_id):
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
    query = TexteReglementaire.query
    q = filters.get('q', '').strip()
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                TexteReglementaire.code.ilike(like),
                TexteReglementaire.titre.ilike(like),
                TexteReglementaire.description.ilike(like))
        )
    domaine_id = filters.get('domaine_id')
    if domaine_id:
        domaine = db.session.get(Domaine, domaine_id)
        if domaine:
            # Filtrer par domaine_id OU par le champ texte domaine (insensible à la casse)
            query = query.filter(
                db.or_(
                    TexteReglementaire.domaine_id == domaine_id,
                    TexteReglementaire.domaine.ilike(domaine.nom))
            )
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
    counts = {'all': total, 'linked': 0, 'unlinked': 0, 'to_evaluate': 0, 'evaluated': 0}
    enriched = []
    for t in all_textes:
        v = t.version_active
        is_new = t.date_creation and t.date_creation.date() >= cutoff if t.date_creation else False
        has_update = v and v.date_publication and v.date_publication >= cutoff if v and v.date_publication else False
        link_state = _compute_library_linkage(current_user.entreprise_id, t.id, v.id if v else None)
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
    per_page = filters.get('per_page', 20)
    page = filters.get('page', 1)
    total_filtered = len(enriched)
    pages = max(1, (total_filtered + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    # Tri : d'abord les liés, puis par date de mise à jour
    def _sort_key(item):
        # linked/evaluated = 0 (premier), unlinked = 1 (après)
        link_order = 0 if item['link_state'] in ('linked', 'evaluated') else 1
        # date de dernière version pour le tri chronologique
        v = item['version_active']
        date_val = v.date_publication if v and v.date_publication else item['texte'].date_creation or date.min
        return (link_order, -(date_val.toordinal() if hasattr(date_val, 'toordinal') else 0))

    enriched.sort(key=_sort_key)

    # Pagination après le tri
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
@access_required()
def library_all():
    filters = _parse_library_filters()
    filters['status'] = request.args.get('status', 'all')
    return _render_library('all', filters)


@textes.route('/bibliotheque/nouveaux-textes')
@access_required()
def library_new():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('new', filters)


@textes.route('/bibliotheque/mises-a-jour-recentes')
@access_required()
def library_recent():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('recent', filters)


@textes.route('/bibliotheque/article/<int:article_id>', methods=['GET', 'POST'])
@access_required()
def article_detail(article_id):
    from app.models.nonconformite import NonConformite as NCModel
    from app.models.proofs import ProofMaster, ProofReference
    from app.models.actions import ActionCorrective
    from app.models import Utilisateur as UserModel
    from datetime import datetime as dt

    article = Article.query.get_or_404(article_id)
    version = article.version if article else None
    texte = version.texte if version else None

    eid = current_user.entreprise_id
    ev_q = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
        EvaluationArticle.conforme == ConformiteEnum.NON_CONFORME,
    )
    evals = ev_q.order_by(EvaluationArticle.date_evaluation.desc().nullslast()).all()
    nc_eval_ids = {nc.evaluation_id for nc in NCModel.query.filter_by(entreprise_id=eid).all() if nc.evaluation_id}
    nc_evs = [ev for ev in evals if ev.id not in nc_eval_ids]

    evaluation = None
    for ev in nc_evs:
        if ev.article_id == article_id:
            evaluation = ev
            break

    if request.method == 'POST' and evaluation:
        conforme_val = request.form.get('conforme')
        if conforme_val:
            evaluation.conforme = ConformiteEnum[conforme_val]
        applicable_val = request.form.get('applicable')
        if applicable_val:
            from app.models.conformite import ApplicabiliteEnum
            evaluation.applicable = ApplicabiliteEnum[applicable_val]
        evaluation.observation = request.form.get('observation', evaluation.observation)
        evaluation.date_evaluation = dt.utcnow()
        evaluation.evalue_par = current_user.id
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
        return redirect(url_for('textes.article_detail', article_id=article_id))

    nc_articles = [ev.article_id for ev in nc_evs]
    current_idx = nc_articles.index(article_id) if article_id in nc_articles else -1
    next_article_id = nc_articles[current_idx + 1] if current_idx >= 0 and current_idx < len(nc_articles) - 1 else None
    prev_article_id = nc_articles[current_idx - 1] if current_idx > 0 else None

    stats = {
        'total': len(nc_evs),
        'current': current_idx + 1 if current_idx >= 0 else 0,
        'conforme': 0,
        'non_conforme': len(nc_evs),
        'non_applicable': 0,
        'evalue': len(nc_evs),
    }

    proofs = []
    actions = []
    if evaluation:
        refs = ProofReference.query.filter_by(
            entity_type='evaluation_article', entity_id=evaluation.id
        ).all()
        for r in refs:
            proofs.append({
                'id': r.id,
                'proof_id': r.proof_master_id,
                'nom_fichier': r.proof_master.nom_fichier if r.proof_master else '?',
                'date_attached': r.date_attached.strftime('%d/%m/%Y') if r.date_attached else '',
            })
        actions = ActionCorrective.query.filter_by(
            source_type='evaluation_article', source_id=evaluation.id
        ).order_by(ActionCorrective.date_creation.desc()).all()

    responsables = UserModel.query.filter_by(entreprise_id=eid).all()

    return render_template(
        'textes/article_detail.html',
        article=article,
        version=version,
        texte=texte,
        evaluation=evaluation,
        nc_evs=nc_evs,
        next_article_id=next_article_id,
        prev_article_id=prev_article_id,
        stats=stats,
        proofs=proofs,
        actions=actions,
        responsables=responsables,
    )


@textes.route('/bibliotheque/article/<int:article_id>/proof/attach', methods=['POST'])
@access_required()
def article_attach_proof(article_id):
    from app.models.proofs import ProofReference
    from app.services.proof_service import ProofService
    eid = current_user.entreprise_id
    evaluation = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EvaluationArticle.article_id == article_id,
        EntrepriseTexte.entreprise_id == eid,
    ).first_or_404()
    proof_id = request.json.get('proof_id') if request.is_json else request.form.get('proof_id')
    if proof_id:
        ProofService.attach_proof(
            entreprise_id=eid,
            entity_type='evaluation_article',
            entity_id=evaluation.id,
            proof_id=int(proof_id),
            attached_by=current_user.id,
        )
        db.session.commit()
    return jsonify({'success': True})


@textes.route('/bibliotheque/article/<int:article_id>/proof/liste')
@access_required()
def article_list_proofs(article_id):
    from app.models.proofs import ProofReference
    eid = current_user.entreprise_id
    evaluation = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EvaluationArticle.article_id == article_id,
        EntrepriseTexte.entreprise_id == eid,
    ).first()
    if not evaluation:
        return jsonify([])
    refs = ProofReference.query.filter_by(
        entity_type='evaluation_article', entity_id=evaluation.id
    ).all()
    return jsonify([{
        'id': r.id,
        'proof_id': r.proof_master_id,
        'nom_fichier': r.proof_master.nom_fichier if r.proof_master else '?',
        'date_attached': r.date_attached.strftime('%d/%m/%Y') if r.date_attached else '',
    } for r in refs])


@textes.route('/bibliotheque/article/<int:article_id>/action/add', methods=['POST'])
@access_required()
def article_add_action(article_id):
    from app.models.actions import ActionCorrective
    from datetime import datetime as dt, timedelta
    eid = current_user.entreprise_id
    evaluation = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EvaluationArticle.article_id == article_id,
        EntrepriseTexte.entreprise_id == eid,
    ).first_or_404()
    action = ActionCorrective(
        entreprise_id=eid,
        domaine='hse',
        description=request.form.get('description'),
        source_type='evaluation_article',
        source_id=evaluation.id,
        type_action=request.form.get('type_action', 'corrective'),
        priorite=request.form.get('priorite', 'moyenne'),
        responsable_id=request.form.get('responsable_id', type=int),
        date_echeance=dt.strptime(request.form['date_echeance'], '%Y-%m-%d').date()
        if request.form.get('date_echeance') else None,
    )
    db.session.add(action)
    db.session.commit()
    return jsonify({'success': True, 'action_id': action.id})


@textes.route('/bibliotheque/article/<int:article_id>/actions')
@access_required()
def article_list_actions(article_id):
    from app.models.actions import ActionCorrective
    eid = current_user.entreprise_id
    evaluation = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EvaluationArticle.article_id == article_id,
        EntrepriseTexte.entreprise_id == eid,
    ).first()
    if not evaluation:
        return jsonify([])
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


@textes.route('/bibliotheque/preuves/<int:proof_id>/download')
@access_required()
def veille_preuves_download(proof_id):
    import os
    import mimetypes
    from flask import send_file as flask_send_file, current_app
    from app.models.proofs import ProofMaster
    from app.services.proof_service import ProofService

    proof = ProofMaster.query.filter_by(id=proof_id, entreprise_id=current_user.entreprise_id).first_or_404()

    download_name = proof.nom_fichier
    if '.' not in (download_name or ''):
        download_name = os.path.basename(proof.chemin or download_name)
    mime_type, _ = mimetypes.guess_type(download_name or '')
    mimetype = mime_type or 'application/octet-stream'

    file_stream = ProofService.get_proof_stream(proof.id)
    if file_stream:
        return flask_send_file(file_stream, as_attachment=True, download_name=download_name, mimetype=mimetype)

    if proof.chemin:
        filename = os.path.basename(proof.chemin)
        for base_dir in (
            current_app.config.get('UPLOAD_FOLDER', 'uploads'),
            os.path.join(current_app.root_path, 'uploads'),
        ):
            for subdir in ('preuves', 'documents/preuves'):
                local_path = os.path.join(base_dir, str(proof.entreprise_id), subdir, filename)
                if os.path.exists(local_path):
                    return flask_send_file(local_path, as_attachment=True, download_name=download_name, mimetype=mimetype)

    return jsonify({'success': False, 'error': 'Fichier non trouvé'}), 404


@textes.route('/bibliotheque/preuves/<int:proof_id>/supprimer', methods=['POST'])
@access_required()
def veille_preuves_supprimer(proof_id):
    from app.models.proofs import ProofMaster
    from app.services.proof_service import ProofService

    proof = ProofMaster.query.filter_by(id=proof_id, entreprise_id=current_user.entreprise_id).first_or_404()
    ProofService.delete_proof_file(proof.id)
    db.session.delete(proof)
    db.session.commit()
    return jsonify({'success': True})


@textes.route('/bibliotheque/preuves/upload', methods=['POST'])
@access_required()
def veille_preuves_upload():
    from app.models.proofs import ProofMaster
    from app.services.proof_service import ProofService
    from werkzeug.utils import secure_filename
    from io import BytesIO

    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': 'Fichier invalide'}), 400

    eid = current_user.entreprise_id
    nom_fichier = request.form.get('nom_fichier') or secure_filename(file.filename)

    if not nom_fichier or '.' not in nom_fichier:
        import os
        _, ext = os.path.splitext(secure_filename(file.filename))
        if ext:
            nom_fichier = (nom_fichier or 'document') + ext

    file_obj = BytesIO(file.read())

    try:
        proof = ProofService.create_or_reuse_proof(
            entreprise_id=eid,
            nom_fichier=nom_fichier,
            file_obj=file_obj,
            domaine='hse',
            description=request.form.get('description', ''),
            categorie=request.form.get('categorie', ''),
            uploaded_by=current_user.id,
        )

        validite = request.form.get('validite')
        if validite and proof:
            from datetime import datetime as dt
            proof.validite = dt.strptime(validite, '%Y-%m-%d').date()

        db.session.commit()
        return jsonify({'success': True, 'proof_id': proof.id})
    except Exception as e:
        db.session.rollback()
        import logging
        logging.getLogger(__name__).exception("Erreur upload preuve veille")
        return jsonify({'success': False, 'error': str(e)}), 500


@textes.route('/bibliotheque/preuves')
@access_required()
def veille_preuves():
    import os
    from datetime import date, timedelta
    from app.models.proofs import ProofMaster, ProofReference

    eid = current_user.entreprise_id
    today = date.today()
    horizon = today + timedelta(days=30)

    proofs = ProofMaster.query.filter_by(entreprise_id=eid).order_by(ProofMaster.date_creation.desc()).all()

    proof_ids = [p.id for p in proofs]
    refs_by_proof = {}
    if proof_ids:
        refs = ProofReference.query.filter(
            ProofReference.proof_master_id.in_(proof_ids),
            ProofReference.entity_type == 'evaluation_article',
        ).all()
        for r in refs:
            refs_by_proof.setdefault(r.proof_master_id, []).append(r)

    ev_ids = list({r.entity_id for r in refs_by_proof.values() for r in r})
    ev_by_id = {}
    if ev_ids:
        evals = EvaluationArticle.query.filter(EvaluationArticle.id.in_(ev_ids)).all()
        ev_by_id = {e.id: e for e in evals}

    upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), str(eid), 'preuves')
    total_bytes = 0
    proof_data = []
    summary = {'expired': 0, 'expiring_soon': 0, 'valid': 0, 'no_date': 0}

    for p in proofs:
        ev_refs = refs_by_proof.get(p.id, [])
        linked_articles = []
        for r in ev_refs:
            ev = ev_by_id.get(r.entity_id)
            if ev:
                linked_articles.append({
                    'article_numero': ev.article.numero_article if ev.article else '?',
                    'texte_titre': ev.entreprise_texte.version.texte.titre[:60] if ev.entreprise_texte and ev.entreprise_texte.version and ev.entreprise_texte.version.texte else '',
                })

        proof_state = 'valid'
        if p.validite:
            if p.validite < today:
                proof_state = 'expired'
                summary['expired'] += 1
            elif p.validite <= horizon:
                proof_state = 'expiring_soon'
                summary['expiring_soon'] += 1
            else:
                proof_state = 'valid'
                summary['valid'] += 1
        else:
            proof_state = 'no_date'
            summary['no_date'] += 1

        file_size = p.taille_bytes
        if not file_size and p.chemin:
            filename = os.path.basename(p.chemin)
            local_path = os.path.join(upload_dir, filename)
            if not os.path.exists(local_path):
                local_path = os.path.join(upload_dir, '..', 'documents', 'preuves', filename)
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)

        proof_data.append({
            'proof': p,
            'refs_count': ProofReference.query.filter_by(proof_master_id=p.id).count(),
            'linked_articles': linked_articles,
            'proof_state': proof_state,
            'file_size': file_size,
        })

    total_files = len(proofs)
    storage_mb = round(total_bytes / (1024.0 * 1024.0), 2) if total_bytes else 0

    return render_template('textes/veille_preuves.html',
        proofs=proof_data,
        summary=summary,
        total_files=total_files,
        storage_mb=storage_mb,
        total_bytes=total_bytes,
        today=today,
    )


@textes.route('/bibliotheque/non-conformites')
@access_required()
def veille_non_conformites():
    from app.models.nonconformite import NonConformite
    eid = current_user.entreprise_id

    ev_q = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
        EvaluationArticle.conforme == ConformiteEnum.NON_CONFORME,
    )
    _article_joined = False

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        ev_q = ev_q.join(Article, EvaluationArticle.article_id == Article.id).filter(
            db.or_(
                Article.contenu.ilike(like),
                Article.resume_article.ilike(like),
            )
        )
        _article_joined = True

    domaine = request.args.get('domaine')
    if domaine:
        if not _article_joined:
            ev_q = ev_q.join(Article, EvaluationArticle.article_id == Article.id)
        ev_q = ev_q.join(TexteVersion, Article.texte_version_id == TexteVersion.id)\
                   .join(TexteReglementaire, TexteVersion.texte_id == TexteReglementaire.id)\
                   .filter(TexteReglementaire.domaine.ilike(domaine))

    evals = ev_q.order_by(EvaluationArticle.date_evaluation.desc().nullslast()).all()

    nc_eval_ids = {nc.evaluation_id for nc in
                   NonConformite.query.filter_by(entreprise_id=eid).all()
                   if nc.evaluation_id}

    data = []
    for ev in evals:
        if ev.id in nc_eval_ids:
            continue
        article = ev.article
        version = article.version if article else None
        texte = version.texte if version else None
        data.append({
            'evaluation': ev,
            'article': article,
            'version': version,
            'texte': texte,
        })

    total = len(data)
    per_page = request.args.get('per_page', 20, type=int)
    page = request.args.get('page', 1, type=int)
    pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    data_page = data[start:start + per_page]

    return render_template(
        'textes/veille_non_conformites.html',
        nonconformites=data_page,
        total=total,
        filters={'q': search, 'domaine': domaine or ''},
        pagination={'page': page, 'pages': pages, 'total': total},
    )


@textes.route('/bibliotheque/veille-dashboard')
@access_required()
def veille_dashboard():
    eid = current_user.entreprise_id
    today = date.today()

    et_list = EntrepriseTexte.query.filter_by(entreprise_id=eid).all()
    total_attribues = len(et_list)

    obligatoires = sum(1 for e in et_list if e.statut_obligation == 'OBLIGATOIRE')
    volontaires = sum(1 for e in et_list if e.statut_obligation == 'VOLONTAIRE')
    hors_perimetre = sum(1 for e in et_list if e.statut_obligation == 'HORS_PERIMETRE')

    all_textes_count = TexteReglementaire.query.count()

    total_articles = 0
    total_evaluated = 0
    total_conformes = 0
    total_non_conformes = 0
    for et in et_list:
        arts = Article.query.filter_by(texte_version_id=et.texte_version_id).count()
        total_articles += arts
        evaluated = [ev for ev in et.evaluations if ev.conforme is not None]
        total_evaluated += len(evaluated)
        total_conformes += sum(1 for ev in evaluated if ev.conforme == ConformiteEnum.CONFORME)
        total_non_conformes += sum(1 for ev in evaluated if ev.conforme == ConformiteEnum.NON_CONFORME)

    taux_conformite = round(total_conformes / total_non_conformes * 100, 1) if total_non_conformes > 0 else 0.0
    couverture_pct = round(total_evaluated / total_articles * 100, 1) if total_articles > 0 else 0.0

    actions_ouvertes = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == eid,
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
    ).count()
    actions_en_retard = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == eid,
        ActionCorrective.statut.notin_(['SOLDE', 'ANNULE']),
        ActionCorrective.date_echeance < today,
    ).count()
    actions_soldees = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == eid,
        ActionCorrective.statut.in_(['SOLDE', 'REALISE']),
    ).count()

    utilisateurs_actifs = Utilisateur.query.filter_by(entreprise_id=eid, actif=True).count()

    notif_recentes = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
    ).order_by(EvaluationArticle.date_evaluation.desc()).limit(5).all()
    evaluations_total = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
    ).count()

    eval_30j = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
        EvaluationArticle.date_evaluation >= today - timedelta(days=30),
    ).count()
    eval_precedent = EvaluationArticle.query.join(EntrepriseTexte).filter(
        EntrepriseTexte.entreprise_id == eid,
        EvaluationArticle.date_evaluation >= today - timedelta(days=60),
        EvaluationArticle.date_evaluation < today - timedelta(days=30),
    ).count()

    from sqlalchemy import func
    actions_par_statut = db.session.query(
        ActionCorrective.statut, func.count(ActionCorrective.id)
    ).filter(
        ActionCorrective.entreprise_id == eid
    ).group_by(ActionCorrective.statut).all()

    from app.models import Role, EntrepriseRole
    users_par_role = db.session.query(
        Role.nom, func.count(Utilisateur.id)
    ).join(Utilisateur, Utilisateur.role_id == Role.id).filter(
        Utilisateur.entreprise_id == eid,
        Utilisateur.actif == True,
    ).group_by(Role.nom).all()

    return render_template(
        'textes/veille_dashboard.html',
        total_attribues=total_attribues,
        all_textes_count=all_textes_count,
        obligatoires=obligatoires,
        volontaires=volontaires,
        hors_perimetre=hors_perimetre,
        taux_conformite=taux_conformite,
        couverture_pct=couverture_pct,
        total_conformes=total_conformes,
        total_non_conformes=total_non_conformes,
        total_evaluated=total_evaluated,
        total_articles=total_articles,
        actions_ouvertes=actions_ouvertes,
        actions_en_retard=actions_en_retard,
        actions_soldees=actions_soldees,
        utilisateurs_actifs=utilisateurs_actifs,
        evaluations_total=evaluations_total,
        notif_recentes=notif_recentes,
        eval_30j=eval_30j,
        eval_precedent=eval_precedent,
        actions_par_statut=actions_par_statut,
        users_par_role=users_par_role,
    )


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
