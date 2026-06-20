import os
import uuid
from flask import render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import ProofMaster, ProofReference, Dossier, TypeDocument, WorkflowLog, Utilisateur
from app.models.systeme import Notification
from app.documents import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import has_permission
from app.services.quota_middleware import check_quota
from app.services.proof_service import ProofService
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func


def _check_ged_access():
    from flask import abort
    from app.models.entreprise import Entreprise
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'ged' not in (entreprise.modules_actifs or []):
        abort(403)


@blueprint.before_request
@login_required
def before_request_ged():
    if request.endpoint and request.endpoint in ('documents.api_actives',):
        return None
    _check_ged_access()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@blueprint.route('/')
@blueprint.route('/gestion')
@login_required
@has_permission('documents.voir')
def gestion():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    eid = current_user.entreprise_id

    base = ProofMaster.query.filter_by(entreprise_id=eid, domaine=domaine, statut='ACTIF')
    all_proofs = base.all()

    q = base

    dossier_id = request.args.get('dossier_id', type=int)
    if dossier_id:
        q = q.filter(ProofMaster.dossier_id == dossier_id)

    type_id = request.args.get('type_id', type=int)
    if type_id:
        q = q.filter(ProofMaster.type_document_id == type_id)

    workflow = request.args.get('workflow')
    if workflow:
        q = q.filter(ProofMaster.workflow_statut == workflow)

    expire = request.args.get('expire')
    if expire:
        today = date.today()
        if expire == '1':
            q = q.filter(ProofMaster.validite.isnot(None), ProofMaster.validite < today)
        elif expire == 'bientot':
            q = q.filter(ProofMaster.validite.isnot(None), ProofMaster.validite >= today,
                         ProofMaster.validite <= date.fromordinal(today.toordinal() + 30))

    sort = request.args.get('sort', 'date')
    if sort == 'nom':
        q = q.order_by(ProofMaster.nom_fichier)
    elif sort == 'validite':
        q = q.order_by(ProofMaster.validite.nullslast())
    else:
        q = q.order_by(ProofMaster.date_creation.desc())

    proofs = q.all()

    stats = {
        'total': len(all_proofs),
        'brouillon': sum(1 for p in all_proofs if p.workflow_statut == 'brouillon'),
        'soumis': sum(1 for p in all_proofs if p.workflow_statut == 'soumis'),
        'approuve': sum(1 for p in all_proofs if p.workflow_statut == 'approuve'),
        'expire': sum(1 for p in all_proofs if p.validite and p.validite < date.today()),
        'expire_bientot': sum(1 for p in all_proofs if p.validite and p.validite >= date.today() and (p.validite - date.today()).days <= 30),
        'en_attente_approbation': sum(1 for p in all_proofs if p.workflow_statut == 'soumis' and p.workflow_approbateur_id == current_user.id),
    }

    dossiers = Dossier.query.filter_by(
        entreprise_id=eid, domaine=domaine
    ).order_by(Dossier.nom).all()

    types_doc = TypeDocument.query.filter_by(
        entreprise_id=eid, domaine=domaine
    ).order_by(TypeDocument.nom).all()

    approbateurs = Utilisateur.query.filter_by(entreprise_id=eid, actif=True).all()

    stats = {
        'total': len(proofs),
        'brouillon': sum(1 for p in proofs if p.workflow_statut == 'brouillon'),
        'soumis': sum(1 for p in proofs if p.workflow_statut == 'soumis'),
        'approuve': sum(1 for p in proofs if p.workflow_statut == 'approuve'),
        'expire': sum(1 for p in proofs if p.validite and p.validite < date.today()),
        'expire_bientot': sum(1 for p in proofs if p.validite and p.validite >= date.today() and (p.validite - date.today()).days <= 30),
        'en_attente_approbation': sum(1 for p in proofs if p.workflow_statut == 'soumis' and p.workflow_approbateur_id == current_user.id),
    }

    return render_template(
        'documents/gestion.html',
        proofs=proofs, dossiers=dossiers, types_doc=types_doc,
        approbateurs=approbateurs, stats=stats, domaine=domaine,
        today=date.today(),
    )


# ---------------------------------------------------------------------------
# Folder management
# ---------------------------------------------------------------------------

@blueprint.route('/api/dossiers')
@login_required
@has_permission('documents.voir')
def api_dossiers():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    dossiers = Dossier.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    ).order_by(Dossier.nom).all()

    def build_tree(parent_id=None):
        items = [d for d in dossiers if d.parent_id == parent_id]
        result = []
        for d in items:
            children = build_tree(d.id)
            doc_count = ProofMaster.query.filter_by(
                dossier_id=d.id, entreprise_id=current_user.entreprise_id, statut='ACTIF'
            ).count()
            result.append({
                'id': d.id,
                'nom': d.nom,
                'description': d.description,
                'parent_id': d.parent_id,
                'doc_count': doc_count,
                'children': children,
                'date_creation': d.date_creation.isoformat() if d.date_creation else None,
            })
        return result

    return jsonify(build_tree(None))


@blueprint.route('/api/dossiers/create', methods=['POST'])
@login_required
@has_permission('documents.upload')
def dossier_create():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    nom = request.form.get('nom', '').strip()
    if not nom:
        flash('Le nom du dossier est requis.', 'danger')
        return redirect(url_for('documents.gestion'))
    dossier = Dossier(
        nom=nom,
        description=request.form.get('description'),
        parent_id=request.form.get('parent_id', type=int) or None,
        entreprise_id=current_user.entreprise_id,
        domaine=domaine,
    )
    db.session.add(dossier)
    db.session.commit()
    flash(f'Dossier "{nom}" créé avec succès.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/api/dossiers/<int:dossier_id>/rename', methods=['POST'])
@login_required
@has_permission('documents.upload')
def dossier_rename(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    nom = request.form.get('nom', '').strip()
    if not nom:
        return jsonify({'success': False, 'error': 'Le nom est requis'}), 400
    dossier.nom = nom
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dossiers/<int:dossier_id>/move', methods=['POST'])
@login_required
@has_permission('documents.upload')
def dossier_move(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    new_parent_id = request.form.get('parent_id', type=int) or None
    if new_parent_id == dossier_id:
        return jsonify({'success': False, 'error': 'Impossible de déplacer un dossier sur lui-même'}), 400
    dossier.parent_id = new_parent_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dossiers/<int:dossier_id>/delete', methods=['POST'])
@login_required
@has_permission('documents.archiver')
def dossier_delete(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    ProofMaster.query.filter_by(dossier_id=dossier_id).update({'dossier_id': None})
    Dossier.query.filter_by(parent_id=dossier_id).update({'parent_id': None})
    db.session.delete(dossier)
    db.session.commit()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Document upload (enhanced with folder + type)
# ---------------------------------------------------------------------------

@blueprint.route('/upload', methods=['POST'])
@login_required
@has_permission('documents.upload')
@check_quota('documents')
def upload():
    """
    Upload un document vers la GED.

    Utilise StorageService pour le stockage (MINIO ou local).
    Le fichier est passé directement au ProofService qui gère
    la détection de doublons et le stockage.
    """
    from flask import session as flask_session
    domaine = flask_session.get('domaine_actif', 'hse')
    eid = current_user.entreprise_id

    if 'file' not in request.files:
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(url_for('documents.gestion'))

    file = request.files['file']
    if not file.filename:
        flash('Fichier invalide.', 'danger')
        return redirect(url_for('documents.gestion'))

    original_filename = secure_filename(file.filename)

    # Générer numéro document auto
    last_num = db.session.query(func.max(ProofMaster.id)).filter_by(entreprise_id=eid).scalar() or 0
    numero_doc = f"DOC-{datetime.utcnow().strftime('%Y%m')}-{last_num + 1:04d}"

    # Upload via ProofService (utilise StorageService en interne)
    proof = ProofService.create_or_reuse_proof(
        entreprise_id=eid,
        nom_fichier=original_filename,
        file_obj=file.stream,
        domaine=domaine,
        description=request.form.get('description'),
        validite=datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        if request.form.get('validite') else None,
        uploaded_by=current_user.id,
        categorie=request.form.get('categorie'),
    )

    proof.dossier_id = request.form.get('dossier_id', type=int) or None
    proof.type_document_id = request.form.get('type_document_id', type=int) or None
    proof.numero_document = numero_doc
    proof.mots_cles = request.form.get('mots_cles')
    proof.notes = request.form.get('notes')
    proof.workflow_statut = request.form.get('workflow_statut', 'brouillon')
    proof.workflow_approbateur_id = request.form.get('workflow_approbateur_id', type=int) or None
    if proof.workflow_statut == 'soumis' and proof.workflow_approbateur_id:
        proof.date_soumission = datetime.utcnow()
        _log_workflow(proof.id, 'soumis', 'Soumis pour approbation', current_user.id)

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type and 'multipart/form-data' in request.content_type and request.args.get('format') == 'json':
        return jsonify({'success': True, 'proof_id': proof.id})

    flash('Document uploadé avec succès.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


# ---------------------------------------------------------------------------
# Document detail (enhanced)
# ---------------------------------------------------------------------------

@blueprint.route('/<int:proof_id>/detail')
@login_required
@has_permission('documents.voir')
def detail(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    refs = ProofReference.query.filter_by(proof_master_id=proof.id).all()
    workflow_logs = WorkflowLog.query.filter_by(proof_master_id=proof.id).order_by(WorkflowLog.date_action.desc()).all()
    approbateurs = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id, actif=True).all()
    types_doc = TypeDocument.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    dossiers = Dossier.query.filter_by(entreprise_id=current_user.entreprise_id).order_by(Dossier.nom).all()

    # Fetch version chain (remplace_preuve_id)
    versions = []
    v = proof
    while v:
        versions.append(v)
        if v.remplace_preuve_id:
            v = ProofMaster.query.get(v.remplace_preuve_id)
        else:
            v = None

    return render_template(
        'documents/detail.html',
        proof=proof, refs=refs, workflow_logs=workflow_logs,
        approbateurs=approbateurs, types_doc=types_doc,
        dossiers=dossiers, versions=versions,
        today=date.today(),
    )


# ---------------------------------------------------------------------------
# Workflow actions
# ---------------------------------------------------------------------------

def _log_workflow(proof_id, action, commentaire, user_id):
    proof = db.session.get(ProofMaster, proof_id)
    avant = {} if not proof else {
        'workflow_statut': proof.workflow_statut,
        'workflow_approbateur_id': proof.workflow_approbateur_id,
    }
    log = WorkflowLog(
        proof_master_id=proof_id, action=action,
        commentaire=commentaire, utilisateur_id=user_id,
        metadata_avant=avant,
    )
    db.session.add(log)
    db.session.flush()
    return log


@blueprint.route('/<int:proof_id>/soumettre', methods=['POST'])
@login_required
@has_permission('documents.workflow')
def soumettre(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    if proof.workflow_statut != 'brouillon':
        flash('Seul un document en brouillon peut être soumis.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    workflow_modele_id = request.form.get('workflow_modele_id', type=int)
    approbateur_id = request.form.get('approbateur_id', type=int) or proof.workflow_approbateur_id

    if workflow_modele_id:
        from app.workflow_engine.models import WorkflowModele, WorkflowEtape, WorkflowInstance, WorkflowHistorique
        modele = WorkflowModele.query.filter_by(id=workflow_modele_id, entreprise_id=current_user.entreprise_id).first()
        if modele:
            etapes = list(modele.etapes.order_by(WorkflowEtape.ordre).all())
            if etapes:
                premiere = etapes[0]
                deadline = None
                if premiere.delai_jours:
                    deadline = datetime.utcnow() + timedelta(days=premiere.delai_jours)
                instance = WorkflowInstance(
                    entreprise_id=current_user.entreprise_id,
                    modele_id=modele.id,
                    entity_type='documents',
                    entity_id=proof.id,
                    etape_courante_id=premiere.id,
                    demandeur_id=current_user.id,
                    statut='en_cours',
                    date_deadline=deadline,
                )
                db.session.add(instance)
                db.session.flush()
                h = WorkflowHistorique(
                    instance_id=instance.id, etape_id=premiere.id,
                    utilisateur_id=current_user.id, action='creer',
                    commentaire='Document soumis pour approbation',
                )
                db.session.add(h)
                if premiere.role_requis:
                    from app.models.auth import Utilisateur as AuthUtilisateur
                    validateurs = AuthUtilisateur.query.filter_by(
                        entreprise_id=current_user.entreprise_id, actif=True
                    ).all()
                    for v in validateurs:
                        if v.role and v.role.nom and premiere.role_requis.lower() in v.role.nom.lower():
                            notif = Notification(type='workflow', message=f'Nouveau document "{proof.nom_fichier}" à valider (workflow: {modele.nom})', utilisateur_id=v.id)
                            db.session.add(notif)

    if not approbateur_id:
        flash('Veuillez sélectionner un approbateur.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    _log_workflow(proof_id, 'soumis',
                  request.form.get('commentaire', 'Soumis pour approbation'),
                  current_user.id)
    proof.workflow_statut = 'soumis'
    proof.workflow_approbateur_id = approbateur_id
    proof.date_soumission = datetime.utcnow()
    notif = Notification(type='workflow', message=f'Document "{proof.nom_fichier}" soumis pour votre approbation.', utilisateur_id=approbateur_id)
    db.session.add(notif)
    db.session.commit()
    flash('Document soumis pour approbation.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/approuver', methods=['POST'])
@login_required
@has_permission('documents.workflow')
def approuver(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    if proof.workflow_statut != 'soumis':
        flash('Seul un document soumis peut être approuvé.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))
    if proof.workflow_approbateur_id != current_user.id and not (current_user.role and current_user.role.est_systeme):
        flash('Vous n\'êtes pas l\'approbateur de ce document.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    from app.workflow_engine.models import WorkflowInstance as WFInstance, WorkflowHistorique as WFHistorique, WorkflowEtape as WFEtape
    wf_instances = WFInstance.query.filter_by(entity_type='documents', entity_id=proof.id, statut='en_cours').all()
    for wf_inst in wf_instances:
        h = WFHistorique(
            instance_id=wf_inst.id, etape_id=wf_inst.etape_courante_id,
            utilisateur_id=current_user.id, action='approuver',
            commentaire=request.form.get('commentaire', 'Document approuvé'),
        )
        db.session.add(h)
        etapes = list(wf_inst.modele.etapes.order_by(WFEtape.ordre).all())
        current_idx = next((i for i, e in enumerate(etapes) if e.id == wf_inst.etape_courante_id), -1)
        if current_idx < len(etapes) - 1:
            next_etape = etapes[current_idx + 1]
            wf_inst.etape_courante_id = next_etape.id
            if next_etape.delai_jours:
                wf_inst.date_deadline = datetime.utcnow() + timedelta(days=next_etape.delai_jours)
            if wf_inst.demandeur_id:
                notif = Notification(type='workflow', message=f'Workflow "{wf_inst.modele.nom}" : étape "{next_etape.nom}" en attente.', utilisateur_id=wf_inst.demandeur_id)
                db.session.add(notif)
        else:
            wf_inst.statut = 'termine'
            wf_inst.date_fin = datetime.utcnow()
            if wf_inst.demandeur_id:
                notif = Notification(type='workflow', message=f'Workflow "{wf_inst.modele.nom}" terminé avec succès.', utilisateur_id=wf_inst.demandeur_id)
                db.session.add(notif)

    _log_workflow(proof_id, 'approuve',
                  request.form.get('commentaire', 'Document approuvé'),
                  current_user.id)
    proof.workflow_statut = 'approuve'
    proof.date_approbation = datetime.utcnow()
    db.session.commit()
    flash('Document approuvé.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/rejeter', methods=['POST'])
@login_required
@has_permission('documents.workflow')
def rejeter(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    if proof.workflow_statut != 'soumis':
        flash('Seul un document soumis peut être rejeté.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))
    if proof.workflow_approbateur_id != current_user.id and not (current_user.role and current_user.role.est_systeme):
        flash('Vous n\'êtes pas l\'approbateur de ce document.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    commentaire = request.form.get('commentaire', '').strip()
    if not commentaire:
        flash('Veuillez fournir un motif de rejet.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    from app.workflow_engine.models import WorkflowInstance as WFInstance, WorkflowHistorique as WFHistorique
    wf_instances = WFInstance.query.filter_by(entity_type='documents', entity_id=proof.id, statut='en_cours').all()
    for wf_inst in wf_instances:
        h = WFHistorique(
            instance_id=wf_inst.id, etape_id=wf_inst.etape_courante_id,
            utilisateur_id=current_user.id, action='rejeter',
            commentaire=commentaire,
        )
        db.session.add(h)
        wf_inst.statut = 'rejete'
        wf_inst.date_fin = datetime.utcnow()
        if wf_inst.demandeur_id:
            notif = Notification(type='workflow', message=f'Workflow "{wf_inst.modele.nom}" rejeté. Motif : {commentaire}', utilisateur_id=wf_inst.demandeur_id)
            db.session.add(notif)

    _log_workflow(proof_id, 'rejete', commentaire, current_user.id)
    proof.workflow_statut = 'rejete'
    db.session.commit()
    flash('Document rejeté.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/demander-revision', methods=['POST'])
@login_required
@has_permission('documents.workflow')
def demander_revision(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    commentaire = request.form.get('commentaire', '').strip()
    if not commentaire:
        flash('Veuillez fournir des instructions de révision.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    _log_workflow(proof_id, 'revision_demandee', commentaire, current_user.id)
    proof.workflow_statut = 'brouillon'
    db.session.commit()
    flash('Révision demandée. Le document repasse en brouillon.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


# ---------------------------------------------------------------------------
# Document versioning (upload new version)
# ---------------------------------------------------------------------------

@blueprint.route('/<int:proof_id>/nouvelle-version', methods=['POST'])
@login_required
@has_permission('documents.upload')
@check_quota('documents')
def nouvelle_version(proof_id):
    """
    Upload une nouvelle version d'un document.

    L'ancienne version passe en statut 'REMPLACE' et la nouvelle
    est créée avec un numéro de version incrémenté.
    """
    from flask import session as flask_session
    old_proof = tenant_get_or_404(ProofMaster, proof_id)
    domaine = flask_session.get('domaine_actif', 'hse')
    eid = current_user.entreprise_id

    if 'file' not in request.files:
        flash('Aucun fichier sélectionné.', 'danger')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    file = request.files['file']
    if not file.filename:
        flash('Fichier invalide.', 'danger')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    original_filename = secure_filename(file.filename)

    # Incrémenter le numéro de version
    old_version = int(old_proof.version) if old_proof.version and old_proof.version.isdigit() else 1
    new_version = str(old_version + 1)

    # Upload via ProofService (utilise StorageService en interne)
    proof = ProofService.create_or_reuse_proof(
        entreprise_id=eid,
        nom_fichier=original_filename,
        file_obj=file.stream,
        domaine=domaine,
        description=request.form.get('description') or old_proof.description,
        validite=datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        if request.form.get('validite') else old_proof.validite,
        uploaded_by=current_user.id,
        categorie=request.form.get('categorie') or old_proof.categorie,
    )

    proof.dossier_id = old_proof.dossier_id
    proof.type_document_id = old_proof.type_document_id
    proof.numero_document = old_proof.numero_document
    proof.mots_cles = old_proof.mots_cles
    proof.notes = request.form.get('notes') or old_proof.notes
    proof.workflow_statut = 'brouillon'
    proof.version = new_version

    _log_workflow(old_proof.id, 'nouvelle_version',
                  f'Nouvelle version {new_version} uploadée',
                  current_user.id)

    # Archiver l'ancienne version
    old_proof.statut = 'REMPLACE'
    proof.remplace_preuve_id = old_proof.id
    db.session.commit()
    flash(f'Nouvelle version {new_version} créée avec succès.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


# ---------------------------------------------------------------------------
# Document type management
# ---------------------------------------------------------------------------

@blueprint.route('/api/types')
@login_required
@has_permission('documents.voir')
def api_types():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    types = TypeDocument.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    ).order_by(TypeDocument.nom).all()
    return jsonify([{
        'id': t.id, 'nom': t.nom, 'description': t.description,
        'schema_metadonnees': t.schema_metadonnees or {},
    } for t in types])


@blueprint.route('/api/types/create', methods=['POST'])
@login_required
@has_permission('documents.upload')
def type_create():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    nom = request.form.get('nom', '').strip()
    if not nom:
        return jsonify({'success': False, 'error': 'Le nom est requis'}), 400
    existing = TypeDocument.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine, nom=nom
    ).first()
    if existing:
        return jsonify({'success': False, 'error': 'Ce type existe déjà'}), 400
    td = TypeDocument(
        nom=nom, description=request.form.get('description'),
        entreprise_id=current_user.entreprise_id, domaine=domaine,
    )
    db.session.add(td)
    db.session.commit()
    return jsonify({'success': True, 'id': td.id})


@blueprint.route('/api/types/<int:type_id>/update', methods=['POST'])
@login_required
@has_permission('documents.upload')
def type_update(type_id):
    td = TypeDocument.query.filter_by(
        id=type_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    if request.form.get('nom'):
        td.nom = request.form['nom']
    if request.form.get('description') is not None:
        td.description = request.form['description']
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/types/<int:type_id>/delete', methods=['POST'])
@login_required
@has_permission('documents.archiver')
def type_delete(type_id):
    td = TypeDocument.query.filter_by(
        id=type_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    ProofMaster.query.filter_by(type_document_id=type_id).update({'type_document_id': None})
    db.session.delete(td)
    db.session.commit()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Enhanced search / filter API
# ---------------------------------------------------------------------------

@blueprint.route('/api/recherche')
@login_required
@has_permission('documents.voir')
def api_recherche():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    eid = current_user.entreprise_id
    q = ProofMaster.query.filter_by(entreprise_id=eid, domaine=domaine, statut='ACTIF')

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.filter(or_(
            ProofMaster.nom_fichier.ilike(like),
            ProofMaster.description.ilike(like),
            ProofMaster.numero_document.ilike(like),
            ProofMaster.mots_cles.ilike(like),
            ProofMaster.notes.ilike(like),
        ))

    dossier_id = request.args.get('dossier_id', type=int)
    if dossier_id:
        q = q.filter(ProofMaster.dossier_id == dossier_id)

    type_id = request.args.get('type_id', type=int)
    if type_id:
        q = q.filter(ProofMaster.type_document_id == type_id)

    workflow = request.args.get('workflow')
    if workflow:
        q = q.filter(ProofMaster.workflow_statut == workflow)

    categorie = request.args.get('categorie')
    if categorie:
        q = q.filter(ProofMaster.categorie == categorie)

    expire = request.args.get('expire')
    if expire == '1':
        q = q.filter(ProofMaster.validite.isnot(None), ProofMaster.validite < date.today())
    elif expire == 'bientot':
        q = q.filter(ProofMaster.validite.isnot(None), ProofMaster.validite >= date.today(),
                     ProofMaster.validite <= date.fromordinal(date.today().toordinal() + 30))

    sort = request.args.get('sort', 'date')
    if sort == 'nom':
        q = q.order_by(ProofMaster.nom_fichier)
    elif sort == 'validite':
        q = q.order_by(ProofMaster.validite.nullslast())
    else:
        q = q.order_by(ProofMaster.date_creation.desc())

    proofs = q.all()
    return jsonify([{
        'id': p.id,
        'nom_fichier': p.nom_fichier,
        'type': p.type,
        'taille_bytes': p.taille_bytes,
        'description': p.description,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
        'statut': p.statut,
        'workflow_statut': p.workflow_statut,
        'numero_document': p.numero_document,
        'dossier_id': p.dossier_id,
        'type_document_id': p.type_document_id,
        'date_creation': p.date_creation.isoformat() if p.date_creation else None,
        'date_soumission': p.date_soumission.isoformat() if p.date_soumission else None,
        'date_approbation': p.date_approbation.isoformat() if p.date_approbation else None,
        'reference_count': p.reference_count or 0,
        'uploader': p.uploader.prenom + ' ' + p.uploader.nom if p.uploader else None,
        'dossier_nom': p.dossier.nom if p.dossier else None,
        'type_nom': p.type_doc.nom if p.type_doc else None,
        'approbateur': p.approbateur.prenom + ' ' + p.approbateur.nom if p.approbateur else None,
    } for p in proofs])


# ---------------------------------------------------------------------------
# Existing routes (keep as-is or enhanced)
# ---------------------------------------------------------------------------

@blueprint.route('/api/liste')
@login_required
@has_permission('documents.voir')
def api_liste():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine, statut='ACTIF'
    ).order_by(ProofMaster.date_creation.desc()).all()
    return jsonify([{
        'id': p.id, 'nom_fichier': p.nom_fichier, 'type': p.type,
        'taille_bytes': p.taille_bytes, 'description': p.description,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
        'statut': p.statut, 'workflow_statut': p.workflow_statut,
        'numero_document': p.numero_document,
        'date_creation': p.date_creation.isoformat() if p.date_creation else None,
        'reference_count': p.reference_count or 0,
        'uploader': p.uploader.prenom + ' ' + p.uploader.nom if p.uploader else None,
    } for p in proofs])


@blueprint.route('/<int:proof_id>/download')
@login_required
@has_permission('documents.voir')
def download(proof_id):
    """
    Télécharge un document depuis la GED.

    Utilise StorageService pour récupérer le fichier (MINIO ou local).
    Retourne le fichier comme attachment.
    """
    proof = tenant_get_or_404(ProofMaster, proof_id)

    # Utiliser ProofService pour récupérer le stream
    file_stream = ProofService.get_proof_stream(proof.id)
    if not file_stream:
        flash('Fichier introuvable dans le stockage.', 'danger')
        return redirect(url_for('documents.gestion'))

    from flask import send_file
    return send_file(
        file_stream,
        as_attachment=True,
        download_name=proof.nom_fichier,
        mimetype=f'application/{proof.type}' if proof.type else None,
    )


@blueprint.route('/<int:proof_id>/archiver', methods=['POST'])
@login_required
@has_permission('documents.archiver')
def archiver(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    _log_workflow(proof_id, 'archive', 'Document archivé', current_user.id)
    ProofService.archive_proof(proof.id)
    db.session.commit()
    flash('Document archivé.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/supprimer', methods=['POST'])
@login_required
@has_permission('documents.archiver')
def supprimer(proof_id):
    """
    Supprime définitivement un document.

    Supprime le fichier du stockage (MINIO ou local) puis
    l'enregistrement de la base de données.
    """
    proof = tenant_get_or_404(ProofMaster, proof_id)
    ProofService.hard_delete_proof(proof.id)
    db.session.commit()
    flash('Document supprimé définitivement.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/mettre_a_jour', methods=['POST'])
@login_required
@has_permission('documents.upload')
def mettre_a_jour(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    proof.description = request.form.get('description', proof.description)
    if request.form.get('validite'):
        proof.validite = datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
    proof.categorie = request.form.get('categorie', proof.categorie)
    proof.dossier_id = request.form.get('dossier_id', type=int) or proof.dossier_id
    proof.type_document_id = request.form.get('type_document_id', type=int) or proof.type_document_id
    proof.mots_cles = request.form.get('mots_cles', proof.mots_cles)
    proof.notes = request.form.get('notes', proof.notes)
    db.session.commit()
    flash('Document mis à jour.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


@blueprint.route('/api/actives')
@login_required
@has_permission('documents.voir')
def api_actives():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine, statut='ACTIF'
    ).order_by(ProofMaster.nom_fichier).all()
    return jsonify([{
        'id': p.id, 'nom_fichier': p.nom_fichier,
        'description': p.description, 'type': p.type,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
    } for p in proofs])
