from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from . import entreprise_textes
from app import db
from app.models import EntrepriseTexte, Article, EvaluationArticle
from app.utils.permissions import has_permission
from app.utils.observability import log_business_event
from datetime import datetime


def _create_missing_evaluations_for_link(entreprise_texte):
    """Cree les evaluations manquantes pour un lien entreprise-texte."""
    if not entreprise_texte or not entreprise_texte.texte_version_id:
        return 0

    article_ids = [
        row[0]
        for row in db.session.query(Article.id)
        .filter(Article.texte_version_id == entreprise_texte.texte_version_id)
        .all()
    ]
    if not article_ids:
        return 0

    existing_article_ids = {
        row[0]
        for row in db.session.query(EvaluationArticle.article_id)
        .filter(
            EvaluationArticle.entreprise_texte_id == entreprise_texte.id,
            EvaluationArticle.article_id.in_(article_ids),
        )
        .all()
    }

    to_create = [
        EvaluationArticle(
            entreprise_texte_id=entreprise_texte.id,
            article_id=article_id,
        )
        for article_id in article_ids
        if article_id not in existing_article_ids
    ]

    if to_create:
        db.session.add_all(to_create)

    return len(to_create)


def _normalize_link_metadata(form_or_json):
    statut = (form_or_json.get('statut_obligation') or '').strip().upper()
    motif = (form_or_json.get('motif_obligation') or '').strip()
    mode = (form_or_json.get('mode_evaluation') or '').strip().upper()

    valid_statuts = {'OBLIGATOIRE', 'VOLONTAIRE', 'HORS_PERIMETRE'}
    valid_modes = {'PERIMETRE_GLOBAL', 'EVALUATION_ADHOC'}

    return {
        'statut_obligation': statut if statut in valid_statuts else None,
        'motif_obligation': motif or None,
        'mode_evaluation': mode if mode in valid_modes else None,
    }




# @entreprise_textes.route('/k')
# @login_required
# def index():
#     """Liste de suivi entreprise -> textes (scaffold vide)
#     Page minimale qui servira de point d'entree du module.
#     """
#     # TODO: remplacer par une requete reelle vers EntrepriseTexte
#     entreprise_textes_list = EntrepriseTexte.query.filter_by(entreprise_id=current_user.entreprise_id).all()
#     return render_template('entreprise_textes/index.html', items=entreprise_textes_list)


# @entreprise_textes.route('/<int:id>')
# @login_required
# def detail(id):
#     """Detail d'un suivi (placeholder)"""
#     # TODO: charger l'objet EntrepriseTexte depuis la BDD
#     item = None
#     return render_template('entreprise_textes/detail.html', item=item)



@entreprise_textes.route('/link', methods=['POST'])
@login_required
@has_permission('entreprise_textes.lier')
def link_create():
    """Create a EntrepriseTexte linking current_user.entreprise to texte.version_active.

    Expect form fields: texte_id
    """
    texte_id = request.form.get('texte_id') or request.form.get('texte')
    if not texte_id:
        flash('Aucun texte specifie pour le lien.', 'warning')
        return redirect(url_for('textes.index'))

    # Use entreprise_id from current_user
    entreprise_id = current_user.entreprise_id
    if not entreprise_id:
        flash('Votre compte n\'est pas rattache a une entreprise.', 'warning')
        return redirect(url_for('textes.index'))

    payload = request.form if request.form else (request.get_json(silent=True) or {})
    metadata = _normalize_link_metadata(payload)

    # Simple creation; in future avoid duplicates
    et = EntrepriseTexte(
        entreprise_id=entreprise_id,
        texte_version_id=None,  # will be set by caller if needed
        statut_obligation='VOLONTAIRE',
        motif_obligation='Decision client',
        mode_evaluation='EVALUATION_ADHOC',
    )
    if metadata.get('statut_obligation'):
        et.statut_obligation = metadata['statut_obligation']
    if metadata.get('motif_obligation'):
        et.motif_obligation = metadata['motif_obligation']
    if metadata.get('mode_evaluation'):
        et.mode_evaluation = metadata['mode_evaluation']
    # If a version_active exists, try to assign it
    from app.models import TexteReglementaire
    try:
        texte_lookup_id = int(texte_id)
    except (TypeError, ValueError):
        texte_lookup_id = None
    texte = db.session.get(TexteReglementaire, texte_lookup_id) if texte_lookup_id is not None else None
    if texte and texte.version_active:
        et.texte_version_id = texte.version_active.id

    db.session.add(et)
    db.session.commit()
    log_business_event(
        current_app.logger,
        'entreprise_texte_link_created',
        tenant_id=current_user.entreprise_id,
        user_id=current_user.id,
        entreprise_texte_id=et.id,
        texte_version_id=et.texte_version_id,
    )
    flash('Lien cree entre votre entreprise et le texte.', 'success')
    return redirect(url_for('textes.index'))


@entreprise_textes.route('/toggle_link', methods=['POST'])
@login_required
@has_permission('entreprise_textes.lier')
def toggle_link():
    """Toggle link for current user's entreprise and a given texte_version_id.

    Expects JSON or form param 'version_id'. Returns JSON {linked: true/false}.
    """
    # Accept version_id from form data or JSON body (more robust)
    version_id = None
    if request.form and request.form.get('version_id'):
        version_id = request.form.get('version_id')
    else:
        json_body = request.get_json(silent=True) or {}
        version_id = json_body.get('version_id')
    if not version_id:
        return (jsonify({'success': False, 'error': 'version_id manquant'}), 400)

    try:
        version_id = int(version_id)
    except Exception:
        return (jsonify({'success': False, 'error': 'version_id invalide'}), 400)

    entreprise_id = current_user.entreprise_id
    if not entreprise_id:
        return (jsonify({'success': False, 'error': 'Utilisateur non rattache a une entreprise'}), 400)

    payload = request.form if request.form else (request.get_json(silent=True) or {})
    metadata = _normalize_link_metadata(payload)
    unlink_requested = str(payload.get('action') or '').strip().lower() == 'unlink'

    existing = EntrepriseTexte.query.filter_by(entreprise_id=entreprise_id, texte_version_id=version_id).first()
    if existing:
        if unlink_requested:
            existing_id = existing.id
            db.session.delete(existing)
            db.session.commit()
            log_business_event(
                current_app.logger,
                'entreprise_texte_link_removed',
                tenant_id=current_user.entreprise_id,
                user_id=current_user.id,
                entreprise_texte_id=existing_id,
                texte_version_id=version_id,
            )
            return jsonify({'success': True, 'linked': False, 'version_id': version_id})

        for field_name, field_value in metadata.items():
            if field_value is not None:
                setattr(existing, field_name, field_value)
        existing.responsable_id = current_user.id
        existing.derniere_mise_a_jour = datetime.utcnow()
        db.session.commit()
        log_business_event(
            current_app.logger,
            'entreprise_texte_link_updated',
            tenant_id=current_user.entreprise_id,
            user_id=current_user.id,
            entreprise_texte_id=existing.id,
            texte_version_id=version_id,
            statut_obligation=existing.statut_obligation,
            mode_evaluation=existing.mode_evaluation,
        )
        return jsonify({'success': True, 'linked': True, 'version_id': version_id})

    if not metadata.get('statut_obligation') or not metadata.get('motif_obligation') or not metadata.get('mode_evaluation'):
        return jsonify({'success': False, 'error': 'statut_obligation, motif_obligation et mode_evaluation sont requis'}), 400

    new = EntrepriseTexte(
        entreprise_id=entreprise_id,
        texte_version_id=version_id,
        date_attribution=datetime.utcnow(),
        responsable_id=current_user.id,
        statut_obligation=metadata['statut_obligation'],
        motif_obligation=metadata['motif_obligation'],
        mode_evaluation=metadata['mode_evaluation'],
    )
    db.session.add(new)
    db.session.commit()
    log_business_event(
        current_app.logger,
        'entreprise_texte_link_created',
        tenant_id=current_user.entreprise_id,
        user_id=current_user.id,
        entreprise_texte_id=new.id,
        texte_version_id=version_id,
        statut_obligation=new.statut_obligation,
        mode_evaluation=new.mode_evaluation,
    )
    return jsonify({'success': True, 'linked': True, 'version_id': version_id})


@entreprise_textes.route('/evaluate', methods=['POST'])
@login_required
@has_permission('conformite.modifier')
def evaluate_linked_text():
    """Declenche manuellement la creation des evaluations d'un texte lie."""
    version_id = request.form.get('version_id', type=int)
    if not version_id:
        flash('Version de texte manquante pour lancer l\'evaluation.', 'warning')
        return redirect(url_for('textes.index'))

    entreprise_id = current_user.entreprise_id
    if not entreprise_id:
        flash('Votre compte n\'est pas rattache a une entreprise.', 'warning')
        return redirect(url_for('textes.index'))

    entreprise_texte = EntrepriseTexte.query.filter_by(
        entreprise_id=entreprise_id,
        texte_version_id=version_id,
    ).first()

    if not entreprise_texte:
        flash('Le texte doit etre lie a votre entreprise avant evaluation.', 'warning')
        return redirect(url_for('textes.index'))

    try:
        created_count = _create_missing_evaluations_for_link(entreprise_texte)
        db.session.commit()
    except Exception:
        db.session.rollback()
        log_business_event(
            current_app.logger,
            'entreprise_texte_evaluation_generation_failed',
            tenant_id=current_user.entreprise_id,
            user_id=current_user.id,
            entreprise_texte_id=entreprise_texte.id,
            texte_version_id=version_id,
            level='warning',
        )
        flash('Erreur lors de la creation des evaluations.', 'danger')
        return redirect(url_for('textes.index'))

    if created_count > 0:
        flash(f'{created_count} evaluations creees avec succes.', 'success')
    else:
        flash('Toutes les evaluations existent deja pour ce texte.', 'info')

    log_business_event(
        current_app.logger,
        'entreprise_texte_evaluation_generation_completed',
        tenant_id=current_user.entreprise_id,
        user_id=current_user.id,
        entreprise_texte_id=entreprise_texte.id,
        texte_version_id=version_id,
        created_count=created_count,
    )

    return redirect(url_for('conformite.evaluations_texte', texte_id=entreprise_texte.id))
