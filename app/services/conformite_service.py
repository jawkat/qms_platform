import os
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from flask import url_for, current_app
from sqlalchemy.orm import selectinload
from app import db
from app.models import (
    EvaluationArticle, ApplicabiliteEnum, ConformiteEnum,
    EntrepriseTexte, Notification, ProofMaster, ProofReference, Utilisateur
)
from app.utils.notifications import create_notification
from app.services.subscription_service import (
    get_documents_limit_status,
    get_storage_limit_status,
)

DEFAULT_PROOF_VALIDITY_YEARS = 1
DEFAULT_EXPIRATION_REMINDER_DAYS = 30
ALLOWED_UPLOAD_ROOTS = {'textes', 'evaluations', 'preuves_autonomes'}


def _safe_join_upload_path(relative_path):
    if relative_path is None:
        return None

    normalized = os.path.normpath(str(relative_path).strip().replace('\\', '/'))
    if not normalized or normalized == '.':
        return None
    if os.path.isabs(normalized):
        return None
    if normalized == '..' or normalized.startswith('../') or normalized.startswith('..' + os.sep):
        return None

    normalized = normalized.replace('\\', '/')
    if '/' not in normalized:
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if not upload_folder:
            return None
        return os.path.join(upload_folder, normalized)

    if normalized.split('/', 1)[0] not in ALLOWED_UPLOAD_ROOTS:
        return None

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return None

    return os.path.join(upload_folder, normalized)


def normalize_core_dict(d):
    """Normalize applicable/conforme/observation keys to comparable string values."""
    out = {}
    for k in ('applicable', 'conforme', 'observation', 'date_evaluation'):
        v = d.get(k)
        if v is None:
            out[k] = ''
        else:
            out[k] = v.strip() if isinstance(v, str) else str(v)
    return out


def enrich_textes_suivis_scores(textes_suivis):
    """Populate nb_articles and score_conformite on EntrepriseTexte rows."""
    texte_ids = [t.id for t in textes_suivis]
    all_evaluations = EvaluationArticle.query.filter(
        EvaluationArticle.entreprise_texte_id.in_(texte_ids)
    ).all() if texte_ids else []

    eval_by_texte = {}
    for e in all_evaluations:
        eval_by_texte.setdefault(e.entreprise_texte_id, []).append(e)

    for texte in textes_suivis:
        texte.nb_articles = len(texte.version.articles)
        evaluations = eval_by_texte.get(texte.id, [])
        texte.nb_evaluees = 0
        texte.nb_applicables = 0
        texte.nb_conformes = 0
        texte.nb_non_conformes = 0
        texte.nb_en_cours = 0
        texte.coverage_rate = 0
        texte.evaluation_status = 'non_demarre'

        if evaluations:
            texte.nb_evaluees = sum(1 for e in evaluations if e.applicable is not None)
            texte.nb_applicables = sum(1 for e in evaluations if e.applicable == ApplicabiliteEnum.APPLICABLE)
            texte.nb_conformes = sum(
                1
                for e in evaluations
                if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.CONFORME
            )
            texte.nb_non_conformes = sum(
                1
                for e in evaluations
                if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.NON_CONFORME
            )
            texte.nb_en_cours = sum(
                1
                for e in evaluations
                if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.EN_COURS
            )

            texte.score_conformite = (
                texte.nb_conformes / texte.nb_applicables * 100
            ) if texte.nb_applicables > 0 else 0
            texte.coverage_rate = (
                texte.nb_evaluees / texte.nb_articles * 100
            ) if texte.nb_articles > 0 else 0

            if texte.nb_non_conformes > 0:
                texte.evaluation_status = 'risque'
            elif texte.nb_evaluees == 0:
                texte.evaluation_status = 'non_demarre'
            elif texte.nb_evaluees < texte.nb_articles:
                texte.evaluation_status = 'en_cours'
            else:
                texte.evaluation_status = 'termine'
        else:
            texte.score_conformite = None
            texte.coverage_rate = 0
            texte.evaluation_status = 'non_demarre'

    return textes_suivis


def build_evaluation_stats(articles):
    """Build compliance stats for evaluation detail sidebar/cards."""
    stats = {
        'total': len(articles),
        'evaluees': sum(1 for e in articles if e.applicable is not None),
        'applicables': sum(
            1
            for e in articles
            if e.applicable in (ApplicabiliteEnum.APPLICABLE, ApplicabiliteEnum.A_CONFIRMER)
        ),
        'conformes': sum(
            1
            for e in articles
            if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.CONFORME
        ),
        'en_cours': sum(
            1
            for e in articles
            if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.EN_COURS
        ),
        'non_conformes': sum(
            1
            for e in articles
            if e.applicable == ApplicabiliteEnum.APPLICABLE and e.conforme == ConformiteEnum.NON_CONFORME
        ),
        'non_applicables': sum(1 for e in articles if e.applicable == ApplicabiliteEnum.NON_APPLICABLE),
        'a_confirmer': sum(1 for e in articles if e.applicable == ApplicabiliteEnum.A_CONFIRMER),
    }
    stats['score_conformite'] = (stats['conformes'] / stats['applicables'] * 100) if stats['applicables'] > 0 else 0
    return stats


def attach_article_navigation(evaluation):
    """Attach navigation metadata (prev/next/index/total) to current evaluation using targeted queries."""
    from app.models import Article, EvaluationArticle
    from sqlalchemy import func

    # Targeted queries for prev/next
    prev_article = EvaluationArticle.query.join(Article)\
        .filter(EvaluationArticle.entreprise_texte_id == evaluation.entreprise_texte_id)\
        .filter(Article.numero_article < evaluation.article.numero_article)\
        .order_by(Article.numero_article.desc())\
        .first()

    next_article = EvaluationArticle.query.join(Article)\
        .filter(EvaluationArticle.entreprise_texte_id == evaluation.entreprise_texte_id)\
        .filter(Article.numero_article > evaluation.article.numero_article)\
        .order_by(Article.numero_article.asc())\
        .first()

    # Get counts for index
    total_articles = EvaluationArticle.query\
        .filter(EvaluationArticle.entreprise_texte_id == evaluation.entreprise_texte_id)\
        .count()
    
    current_index = EvaluationArticle.query.join(Article)\
        .filter(EvaluationArticle.entreprise_texte_id == evaluation.entreprise_texte_id)\
        .filter(Article.numero_article < evaluation.article.numero_article)\
        .count()

    evaluation.article_index = current_index + 1
    evaluation.total_articles = total_articles
    evaluation.prev_article = prev_article
    evaluation.next_article = next_article
    return evaluation, current_index, total_articles


def build_proof_state_for_documents(documents, reference_date=None):
    """Determine the compliance state of a set of documents based on validity dates."""
    docs = list(documents or [])
    today = reference_date or date.today()
    if not docs:
        return {'state': 'missing', 'expires_at': None}

    validity_dates = [doc.validite for doc in docs if doc.validite]
    if not validity_dates:
        return {'state': 'valid', 'expires_at': None}

    earliest = min(validity_dates)
    if earliest < today:
        state = 'expired'
    elif earliest <= (today + timedelta(days=DEFAULT_EXPIRATION_REMINDER_DAYS)):
        state = 'expiring_soon'
    else:
        state = 'valid'

    return {'state': state, 'expires_at': earliest}


def build_proof_marker(document_id, due_date, kind):
    """Build a unique marker for notifications to avoid duplicates."""
    return f"[DOC:{document_id}][DUE:{due_date.isoformat()}][TYPE:{kind}]"


def notification_exists(user_id, marker):
    """Check if a notification with a specific marker already exists for a user."""
    return (
        Notification.query
        .filter(
            Notification.utilisateur_id == user_id,
            Notification.message.contains(marker),
        )
        .first()
        is not None
    )


def trigger_expiration_reminders(evaluation, user_ids, today=None):
    """Check evaluation proofs and trigger notifications for expiration."""
    if not evaluation or not user_ids:
        return

    docs = list(get_evaluation_attachment_views(evaluation))
    if not docs:
        return

    today = today or date.today()
    eval_marker = f"[EVAL:{evaluation.id}]"

    for doc in docs:
        if not doc.validite:
            continue

        if doc.validite < today:
            marker = build_proof_marker(doc.id, doc.validite, 'EXPIRED')
            message = (
                f"Preuve expirée: '{doc.nom_fichier}' est expirée depuis le "
                f"{doc.validite.strftime('%d/%m/%Y')} {marker} {eval_marker}"
            )
            notification_type = 'danger'
        elif doc.validite <= (today + timedelta(days=DEFAULT_EXPIRATION_REMINDER_DAYS)):
            days_left = (doc.validite - today).days
            marker = build_proof_marker(doc.id, doc.validite, 'REMINDER')
            message = (
                f"Rappel preuve: '{doc.nom_fichier}' expire dans {days_left} jour(s) le "
                f"{doc.validite.strftime('%d/%m/%Y')} {marker} {eval_marker}"
            )
            notification_type = 'warning'
        else:
            continue

        for user_id in user_ids:
            if not user_id or notification_exists(user_id, marker):
                continue
            create_notification(user_id, message, type=notification_type)


def add_years_safe(d, years=1):
    """Add years to a date object, handling leap years."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


def parse_optional_date(raw_value):
    """Parse a date string from form input."""
    value = (raw_value or '').strip()
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


def default_proof_validity_date(evaluation):
    """Compute default validity date for a new proof based on evaluation date."""
    base_date = None
    if evaluation and evaluation.date_evaluation:
        base_date = evaluation.date_evaluation.date() if hasattr(evaluation.date_evaluation, 'date') else evaluation.date_evaluation
    if base_date is None:
        base_date = date.today()
    return add_years_safe(base_date, DEFAULT_PROOF_VALIDITY_YEARS)


def build_attachment_view(document=None, proof_reference=None):
    """Create a unified view object for legacy Documents or ProofReferences."""
    if document is not None:
        return SimpleNamespace(
            id=document.id,
            nom_fichier=document.nom_fichier,
            description=document.description or '',
            validite=document.validite,
            type=document.type or '',
            date_upload=document.date_upload or datetime.utcnow(),
            upload_par=document.upload_par,
            chemin=document.chemin,
            can_delete=True,
            delete_url=url_for('conformite.delete_justificatif', evaluation_id=document.lie_a_id, doc_id=document.id),
            detail_url=url_for('conformite.get_document', doc_id=document.id),
            download_url=url_for('conformite.download_document_direct', doc_id=document.id),
            source='document',
        )

    proof = proof_reference.proof_master if proof_reference else None
    if proof is None:
        return None

    return SimpleNamespace(
        id=proof_reference.id,
        proof_id=proof.id,
        nom_fichier=proof.nom_fichier,
        description=proof_reference.get_description() or proof.description or '',
        validite=proof_reference.get_validite() or proof.validite,
        type=proof.type or '',
        date_upload=proof_reference.date_attached or proof.date_creation or datetime.utcnow(),
        upload_par=proof.upload_par,
        chemin=proof.chemin,
        can_delete=True,
        delete_url=None,
        detail_url=url_for('conformite.preuves_detail', proof_id=proof.id),
        download_url=url_for('conformite.preuves_detail', proof_id=proof.id),
        source='proof',
    )


def get_evaluation_attachment_views(evaluation):
    """Retrieve all attachments (legacy and new) for an evaluation."""
    attachments = []
    for document in evaluation.justificatifs or []:
        attachments.append(build_attachment_view(document=document))
    for proof_reference in evaluation.proof_references or []:
        attachment = build_attachment_view(proof_reference=proof_reference)
        if attachment is not None:
            attachments.append(attachment)
    return attachments


def build_proof_alert_rows(entreprise_id, state_filter='all', show_missing=False):
    """Build a comprehensive list of proof alerts and status for an enterprise."""
    evaluations = (
        EvaluationArticle.query
        .join(EntrepriseTexte)
        .filter(EntrepriseTexte.entreprise_id == entreprise_id)
        .options(
            selectinload(EvaluationArticle.justificatifs),
            selectinload(EvaluationArticle.proof_references).selectinload(ProofReference.proof_master),
        )
        .all()
    )

    today = date.today()
    horizon = today + timedelta(days=DEFAULT_EXPIRATION_REMINDER_DAYS)

    proof_groups = {}
    summary = {
        'total': 0,
        'expired': 0,
        'expiring_soon': 0,
        'missing': 0,
        'valid': 0,
    }

    total_files = 0
    total_bytes = 0
    seen_file_keys = set()

    upload_folder = current_app.config.get('UPLOAD_FOLDER')

    def _state_rank(state_value):
        order = {'expired': 3, 'expiring_soon': 2, 'valid': 1, 'missing': 0}
        return order.get(state_value, 0)

    for evaluation in evaluations:
        attachments = get_evaluation_attachment_views(evaluation)
        proof_state = build_proof_state_for_documents(attachments)
        state = proof_state.get('state')
        summary['total'] += 1
        if state in summary:
            summary[state] += 1

        # Exclure les évaluations sans preuve si on n'a pas demandé à les afficher
        if state == 'missing' and not show_missing:
            continue

        if state_filter != 'all' and state != state_filter:
            if not (show_missing and state == 'missing'):
                continue

        texte_title = None
        article_number = None
        try:
            if evaluation.entreprise_texte and evaluation.entreprise_texte.version and evaluation.entreprise_texte.version.texte:
                texte_title = evaluation.entreprise_texte.version.texte.titre
        except Exception:
            texte_title = None
        try:
            if evaluation.article:
                article_number = evaluation.article.numero_article
        except Exception:
            article_number = None

        docs = list(attachments)
        valid_dates = [doc.validite for doc in docs if doc.validite]
        next_expiration = min(valid_dates) if valid_dates else None

        for doc in docs:
            file_key = (doc.chemin or '').strip() or f'doc:{doc.id}'
            size_bytes = None
            try:
                if upload_folder and doc.chemin:
                    file_path = _safe_join_upload_path(doc.chemin)
                    if os.path.exists(file_path):
                        size_bytes = os.path.getsize(file_path)
            except Exception:
                size_bytes = None

            if file_key not in seen_file_keys:
                seen_file_keys.add(file_key)
                total_files += 1
                if size_bytes and size_bytes > 0:
                    total_bytes += size_bytes

            uploader = db.session.get(Utilisateur, doc.upload_par) if doc.upload_par else None
            uploader_name = f"{uploader.prenom} {uploader.nom}" if uploader else 'N/A'

            group = proof_groups.get(file_key)
            if group is None:
                group = {
                    'file_key': file_key,
                    'document_id': doc.id,
                    'detail_url': doc.detail_url,
                    'download_url': doc.download_url,
                    'can_edit': doc.can_delete,
                    'nom_fichier': doc.nom_fichier,
                    'description': doc.description or '',
                    'size_bytes': size_bytes,
                    'validite': doc.validite,
                    'uploader': uploader_name,
                    'linked_items': [],
                    'linked_index': set(),
                    'state': state,
                    'document_date_upload': doc.date_upload or datetime.utcnow(),
                }
                proof_groups[file_key] = group
            else:
                # Keep the most recent representative row for display/download.
                current_doc_date = doc.date_upload or datetime.utcnow()
                representative_doc_date = group.get('document_date_upload') or datetime.min
                if current_doc_date >= representative_doc_date:
                    group['document_id'] = doc.id
                    group['detail_url'] = doc.detail_url
                    group['download_url'] = doc.download_url
                    group['can_edit'] = doc.can_delete
                    group['nom_fichier'] = doc.nom_fichier
                    group['description'] = doc.description or ''
                    group['size_bytes'] = size_bytes
                    group['validite'] = doc.validite
                    group['uploader'] = uploader_name
                    group['document_date_upload'] = current_doc_date

            linked_key = (evaluation.id, evaluation.article_id, evaluation.entreprise_texte_id)
            if linked_key not in group['linked_index']:
                group['linked_index'].add(linked_key)
                group['linked_items'].append(
                    {
                        'evaluation_id': evaluation.id,
                        'texte_title': texte_title,
                        'article_number': article_number,
                        'state': state,
                        'date_label': evaluation.date_evaluation.strftime('%d/%m/%Y') if getattr(evaluation, 'date_evaluation', None) else '',
                    }
                )

        # Keep a group placeholder per proof and enrich it with the most severe state.
        for doc in docs:
            file_key = (doc.chemin or '').strip() or f'doc:{doc.id}'
            group = proof_groups.get(file_key)
            if not group:
                continue
            if _state_rank(state) > _state_rank(group.get('state')):
                group['state'] = state
            if group.get('validite') is None and doc.validite:
                group['validite'] = doc.validite

    # Compter aussi toutes les preuves ProofMaster de l'entreprise (y compris remplacées/supprimées)
    # pour que les quotas reflètent le vrai stockage occupé sur le disque.
    try:
        all_proofs = ProofMaster.query.filter(
            ProofMaster.entreprise_id == entreprise_id,
        ).all()
        for proof in all_proofs:
            pk = (proof.chemin or '').strip() or f'proof:{proof.id}'
            if pk not in seen_file_keys:
                seen_file_keys.add(pk)
                total_files += 1
                if upload_folder and proof.chemin:
                    try:
                        fp = _safe_join_upload_path(proof.chemin)
                        if os.path.exists(fp):
                            total_bytes += os.path.getsize(fp)
                    except Exception:
                        pass
    except Exception:
        pass

    rows = []
    for group in proof_groups.values():
        valid_dates = [item['validite'] for item in group['linked_items'] if item.get('validite')]
        representative_validite = group.get('validite')
        if representative_validite:
            valid_dates = [representative_validite]
        state = group.get('state', 'valid')
        if valid_dates:
            earliest = min(valid_dates)
            if earliest < today:
                state = 'expired'
            elif earliest <= horizon:
                state = 'expiring_soon'
            else:
                state = 'valid'
        else:
            state = 'valid'

        linked_items = group.get('linked_items', [])
        linked_items.sort(key=lambda item: (item.get('texte_title') or '', item.get('article_number') or 0, item.get('evaluation_id') or 0))

        search_blob = ' '.join(
            filter(
                None,
                [
                    group.get('nom_fichier') or '',
                    group.get('description') or '',
                    ' '.join((item.get('texte_title') or '') for item in linked_items),
                    ' '.join(str(item.get('article_number') or '') for item in linked_items),
                ],
            )
        )

        rows.append(
            {
                'file_key': group.get('file_key'),
                'document_id': group.get('document_id'),
                'detail_url': group.get('detail_url'),
                'download_url': group.get('download_url'),
                'can_edit': group.get('can_edit', False),
                'nom_fichier': group.get('nom_fichier'),
                'description': group.get('description') or '',
                'size_bytes': group.get('size_bytes'),
                'validite': (group.get('validite').strftime('%d/%m/%Y') if group.get('validite') else ''),
                'uploader': group.get('uploader') or 'N/A',
                'state': state,
                'next_expiration': group.get('validite'),
                'linked_items': linked_items,
                'linked_count': len(linked_items),
                'search_blob': search_blob,
            }
        )

    rows.sort(key=lambda item: (item.get('next_expiration') or date.max, item.get('nom_fichier') or ''))

    try:
        attached_proof_ids = {
            ref.proof_master_id
            for ref in ProofReference.query.join(
                EvaluationArticle, ProofReference.entity_id == EvaluationArticle.id
            ).join(
                EntrepriseTexte, EvaluationArticle.entreprise_texte_id == EntrepriseTexte.id
            ).filter(
                ProofReference.entity_type == 'evaluation_article',
                EntrepriseTexte.entreprise_id == entreprise_id,
            ).with_entities(ProofReference.proof_master_id).all()
        }

        orphan_proofs = ProofMaster.query.filter(
            ProofMaster.entreprise_id == entreprise_id,
            ProofMaster.statut == 'ACTIF',
            ~ProofMaster.id.in_(attached_proof_ids) if attached_proof_ids else True,
        ).order_by(ProofMaster.date_creation.desc()).all()

        for proof in orphan_proofs:
            proof_validite = proof.validite
            if proof_validite:
                if proof_validite < today:
                    orphan_state = 'expired'
                elif proof_validite <= horizon:
                    orphan_state = 'expiring_soon'
                else:
                    orphan_state = 'valid'
            else:
                orphan_state = 'valid'

            if state_filter != 'all' and orphan_state != state_filter:
                continue

            uploader = db.session.get(Utilisateur, proof.upload_par) if proof.upload_par else None
            uploader_name = f"{uploader.prenom} {uploader.nom}" if uploader else 'N/A'

            size_bytes = None
            try:
                if upload_folder and proof.chemin:
                    fp = _safe_join_upload_path(proof.chemin)
                    if os.path.exists(fp):
                        size_bytes = os.path.getsize(fp)
            except Exception:
                pass

            summary['total'] += 1
            if orphan_state in summary:
                summary[orphan_state] += 1

            rows.append({
                'file_key': proof.chemin or f'proof:{proof.id}',
                'document_id': None,
                'proof_id': proof.id,
                'detail_url': url_for('conformite.preuves_detail', proof_id=proof.id),
                'download_url': url_for('conformite.download_proof', proof_id=proof.id),
                'can_edit': False,
                'nom_fichier': proof.nom_fichier,
                'description': proof.description or '',
                'size_bytes': size_bytes,
                'validite': proof_validite.strftime('%d/%m/%Y') if proof_validite else '',
                'uploader': uploader_name,
                'state': orphan_state,
                'next_expiration': proof_validite,
                'linked_items': [],
                'linked_count': 0,
                'is_standalone': True,
                'search_blob': f"{proof.nom_fichier or ''} {proof.description or ''}",
            })
    except Exception:
        current_app.logger.exception("Erreur lors de l'inclusion des preuves autonomes dans alertes")

    rows.sort(key=lambda item: (item.get('next_expiration') or date.max, item.get('nom_fichier') or ''))

    try:
        docs_limit_reached, current_docs, docs_limit, docs_plan = get_documents_limit_status(entreprise_id)
    except Exception:
        current_docs = None
        docs_limit = None
        docs_plan = None

    try:
        storage_limit_reached, current_bytes, storage_limit_bytes, storage_plan = get_storage_limit_status(entreprise_id)
    except Exception:
        current_bytes = None
        storage_limit_bytes = None
        storage_plan = None

    totals = {
        'total_files': current_docs if current_docs is not None else total_files,
        'total_bytes': current_bytes if current_bytes is not None else total_bytes,
        'docs_limit': docs_limit,
        'docs_plan': docs_plan,
        'storage_limit_bytes': storage_limit_bytes,
        'storage_plan': storage_plan,
    }

    try:
        cb = totals.get('total_bytes') or 0
        sb = totals.get('storage_limit_bytes')
        totals['storage_mb_used'] = round(cb / (1024.0 * 1024.0), 2)
        totals['storage_mb_limit'] = round(sb / (1024.0 * 1024.0), 2) if sb else None
        if sb and sb > 0:
            totals['storage_pct'] = round((float(cb) / float(sb)) * 100.0, 2)
        else:
            totals['storage_pct'] = None
    except Exception:
        totals['storage_mb_used'] = None
        totals['storage_mb_limit'] = None
        totals['storage_pct'] = None

    try:
        docs_used = totals.get('total_files') or 0
        docs_limit_val = totals.get('docs_limit')
        totals['docs_used'] = docs_used
        totals['docs_limit'] = docs_limit_val
        if docs_limit_val and docs_limit_val > 0:
            totals['docs_pct'] = round((float(docs_used) / float(docs_limit_val)) * 100.0, 2)
        else:
            totals['docs_pct'] = None
    except Exception:
        totals['docs_used'] = None
        totals['docs_pct'] = None

    return rows, summary, totals
