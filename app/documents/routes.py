import os
import uuid
from flask import render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_login import current_user
from app import db
from app.models import ProofMaster, ProofReference, Dossier, TypeDocument, WorkflowLog, Utilisateur
from app.documents import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.services.quota_middleware import check_quota
from app.services.proof_service import ProofService
from app.services.document_service import DocumentService
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from app.schemas.documents import DossierSchema, TypeDocumentSchema, ProofMasterSchema
from sqlalchemy import or_, func


class ProofMasterResource(BaseResource):
    model = ProofMaster
    schema = ProofMasterSchema
    search_fields = ['nom_fichier', 'description', 'numero_document', 'mots_cles', 'notes']
    filter_fields = {
        'statut': 'statut', 'domaine': 'domaine', 'dossier_id': 'dossier_id',
        'type_document_id': 'type_document_id', 'workflow_statut': 'workflow_statut',
        'categorie': 'categorie',
    }
    sort_field = 'date_creation'
    sort_dir = 'desc'


class DossierResource(BaseResource):
    model = Dossier
    schema = DossierSchema
    search_fields = ['nom', 'description']
    filter_fields = {'domaine': 'domaine'}
    sort_field = 'nom'
    sort_dir = 'asc'


class TypeDocumentResource(BaseResource):
    model = TypeDocument
    schema = TypeDocumentSchema
    search_fields = ['nom', 'description']
    filter_fields = {'domaine': 'domaine'}
    sort_field = 'nom'
    sort_dir = 'asc'


def _check_ged_access():
    from flask import abort
    from app.models.entreprise import Entreprise
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'ged' not in (entreprise.modules_actifs or []):
        abort(403)


@blueprint.before_request
@access_required()
def before_request_ged():
    if request.endpoint and request.endpoint in ('documents.api_actives',):
        return None
    _check_ged_access()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@blueprint.route('/')
@blueprint.route('/gestion')
@access_required(permission='documents.voir')
def gestion():
    statut_filter = request.args.get('statut', 'ACTIF')
    if statut_filter not in ('ACTIF', 'ARCHIVE'):
        statut_filter = 'ACTIF'
    base = ProofMaster.query.filter_by(entreprise_id=current_user.entreprise_id, statut=statut_filter)
    all_proofs = base.all()
    archive_count = ProofMaster.query.filter_by(entreprise_id=current_user.entreprise_id, statut='ARCHIVE').count()

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

    stats = DocumentService.compute_stats(current_user.entreprise_id, proofs)
    stats['en_attente_approbation'] = DocumentService.compute_pending_approvals(proofs, current_user.id)

    dossiers = Dossier.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Dossier.nom).all()

    types_doc = TypeDocument.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(TypeDocument.nom).all()

    approbateurs = Utilisateur.query.filter_by(actif=True).all()

    return render_template(
        'documents/gestion.html',
        proofs=proofs, dossiers=dossiers, types_doc=types_doc,
        approbateurs=approbateurs, stats=stats,
        today=date.today(), archive_count=archive_count,
        show_archives=(statut_filter == 'ARCHIVE'),
    )


# ---------------------------------------------------------------------------
# Folder management
# ---------------------------------------------------------------------------

@blueprint.get('/api/dossiers')
@access_required(permission='documents.voir')
def api_dossiers():
    """Arborescence des dossiers de la GED"""
    domaine = request.args.get('domaine')
    return DocumentService.build_dossier_tree(current_user.entreprise_id, domaine)


@blueprint.route('/api/dossiers/create', methods=['POST'])
@access_required(permission='documents.upload')
def dossier_create():
    nom = request.form.get('nom', '').strip()
    if not nom:
        flash('Le nom du dossier est requis.', 'danger')
        return redirect(url_for('documents.gestion'))
    dossier = Dossier(
        nom=nom,
        description=request.form.get('description'),
        parent_id=request.form.get('parent_id', type=int) or None,
        entreprise_id=current_user.entreprise_id,
    )
    db.session.add(dossier)
    db.session.commit()
    flash(f'Dossier "{nom}" cree avec succes.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/api/dossiers/<int:dossier_id>/rename', methods=['POST'])
@access_required(permission='documents.upload')
def dossier_rename(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id
    ).first_or_404()
    nom = request.form.get('nom', '').strip()
    if not nom:
        return jsonify({'success': False, 'error': 'Le nom est requis'}), 400
    dossier.nom = nom
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dossiers/<int:dossier_id>/move', methods=['POST'])
@access_required(permission='documents.upload')
def dossier_move(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id
    ).first_or_404()
    new_parent_id = request.form.get('parent_id', type=int) or None
    if new_parent_id == dossier_id:
        return jsonify({'success': False, 'error': 'Impossible de déplacer un dossier sur lui-même'}), 400
    dossier.parent_id = new_parent_id
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dossiers/<int:dossier_id>/delete', methods=['POST'])
@access_required(permission='documents.archiver')
def dossier_delete(dossier_id):
    dossier = Dossier.query.filter_by(
        id=dossier_id
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
@access_required(permission='documents.upload')
@check_quota('documents')
def upload():
    """Upload un document vers la GED."""
    if 'file' not in request.files:
        flash('Aucun fichier selectionne.', 'danger')
        return redirect(url_for('documents.gestion'))

    file = request.files['file']
    if not file.filename:
        flash('Fichier invalide.', 'danger')
        return redirect(url_for('documents.gestion'))

    original_filename = secure_filename(file.filename)
    numero_doc = DocumentService.generate_numero_document()

    proof = ProofService.create_or_reuse_proof(
        entreprise_id=current_user.entreprise_id,
        nom_fichier=original_filename,
        file_obj=file.stream,
        description=request.form.get('description'),
        validite=datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        if request.form.get('validite') else None,
        uploaded_by=current_user.id,
        categorie=request.form.get('categorie'),
    )

    DocumentService.apply_upload_metadata(proof, request.form, current_user.id, numero_doc)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type and 'multipart/form-data' in request.content_type and request.args.get('format') == 'json':
        return jsonify({'success': True, 'proof_id': proof.id})

    flash('Document upload\u00e9 avec succ\u00e8s.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


# ---------------------------------------------------------------------------
# Document detail (enhanced)
# ---------------------------------------------------------------------------

@blueprint.route('/<int:proof_id>/detail')
@access_required(permission='documents.voir')
def detail(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    refs = ProofReference.query.filter_by(proof_master_id=proof.id).all()
    workflow_logs = WorkflowLog.query.filter_by(proof_master_id=proof.id).order_by(WorkflowLog.date_creation.desc()).all()
    approbateurs = Utilisateur.query.filter_by(actif=True).all()
    types_doc = TypeDocument.query.all()
    dossiers = Dossier.query.order_by(Dossier.nom).all()

    versions = DocumentService.build_version_chain(proof)

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
    return DocumentService.log_workflow(proof_id, action, commentaire, user_id)


@blueprint.route('/<int:proof_id>/soumettre', methods=['POST'])
@access_required(permission='documents.workflow')
def soumettre(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    if proof.workflow_statut != 'brouillon':
        flash('Seul un document en brouillon peut être soumis.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    workflow_modele_id = request.form.get('workflow_modele_id', type=int)
    approbateur_id = request.form.get('approbateur_id', type=int) or proof.workflow_approbateur_id

    if workflow_modele_id:
        from app.models import WorkflowModele, WorkflowEtape, WorkflowInstance, WorkflowHistorique
        modele = WorkflowModele.query.filter_by(id=workflow_modele_id).first()
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
                        actif=True
                    ).all()
                    for v in validateurs:
                        if v.role and v.role.nom and premiere.role_requis.lower() in v.role.nom.lower():
                            from app.utils.notifications import create_notification
                            create_notification(v.id, f'Nouveau document "{proof.nom_fichier}" à valider (workflow: {modele.nom})', type='workflow')

    if not approbateur_id:
        flash('Veuillez sélectionner un approbateur.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    _log_workflow(proof_id, 'soumis',
                  request.form.get('commentaire', 'Soumis pour approbation'),
                  current_user.id)
    proof.workflow_statut = 'soumis'
    proof.workflow_approbateur_id = approbateur_id
    proof.date_soumission = datetime.utcnow()
    from app.utils.notifications import create_notification
    create_notification(approbateur_id, f'Document "{proof.nom_fichier}" soumis pour votre approbation.', type='workflow')
    db.session.commit()
    flash('Document soumis pour approbation.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/approuver', methods=['POST'])
@access_required(permission='documents.workflow')
def approuver(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    if proof.workflow_statut != 'soumis':
        flash('Seul un document soumis peut être approuvé.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))
    if proof.workflow_approbateur_id != current_user.id and not (current_user.role and current_user.role.est_systeme):
        flash('Vous n\'êtes pas l\'approbateur de ce document.', 'warning')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    from app.models import WorkflowInstance as WFInstance, WorkflowHistorique as WFHistorique, WorkflowEtape as WFEtape
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
                from app.utils.notifications import create_notification
                create_notification(wf_inst.demandeur_id, f'Workflow "{wf_inst.modele.nom}" : étape "{next_etape.nom}" en attente.', type='workflow')
        else:
            wf_inst.statut = 'termine'
            wf_inst.date_fin = datetime.utcnow()
            if wf_inst.demandeur_id:
                from app.utils.notifications import create_notification
                create_notification(wf_inst.demandeur_id, f'Workflow "{wf_inst.modele.nom}" terminé avec succès.', type='workflow')

    _log_workflow(proof_id, 'approuve',
                  request.form.get('commentaire', 'Document approuvé'),
                  current_user.id)
    proof.workflow_statut = 'approuve'
    proof.date_approbation = datetime.utcnow()
    db.session.commit()
    flash('Document approuvé.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/rejeter', methods=['POST'])
@access_required(permission='documents.workflow')
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
            from app.utils.notifications import create_notification
            create_notification(wf_inst.demandeur_id, f'Workflow "{wf_inst.modele.nom}" rejeté. Motif : {commentaire}', type='workflow')

    _log_workflow(proof_id, 'rejete', commentaire, current_user.id)
    proof.workflow_statut = 'rejete'
    db.session.commit()
    flash('Document rejeté.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof_id))


@blueprint.route('/<int:proof_id>/demander-revision', methods=['POST'])
@access_required(permission='documents.workflow')
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
@access_required(permission='documents.upload')
@check_quota('documents')
def nouvelle_version(proof_id):
    """Upload une nouvelle version d'un document."""
    old_proof = tenant_get_or_404(ProofMaster, proof_id)
    if 'file' not in request.files:
        flash('Aucun fichier selectionne.', 'danger')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    file = request.files['file']
    if not file.filename:
        flash('Fichier invalide.', 'danger')
        return redirect(url_for('documents.detail', proof_id=proof_id))

    original_filename = secure_filename(file.filename)

    old_version = int(old_proof.version) if old_proof.version and old_proof.version.isdigit() else 1
    new_version = str(old_version + 1)

    proof = ProofService.create_or_reuse_proof(
        entreprise_id=current_user.entreprise_id,
        nom_fichier=original_filename,
        file_obj=file.stream,
        description=request.form.get('description') or old_proof.description,
        validite=datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        if request.form.get('validite') else old_proof.validite,
        uploaded_by=current_user.id,
        categorie=request.form.get('categorie') or old_proof.categorie,
    )

    DocumentService.create_new_version(old_proof, proof, request.form, current_user.id)
    db.session.commit()
    flash(f'Nouvelle version {new_version} cr\u00e9\u00e9e avec succ\u00e8s.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


# ---------------------------------------------------------------------------
# Document type management
# ---------------------------------------------------------------------------

@blueprint.get('/api/types')
@access_required(permission='documents.voir')
@blueprint.response(200, TypeDocumentSchema(many=True))
def api_types():
    """Liste des types de documents disponibles"""
    return TypeDocument.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(TypeDocument.nom).all()


@blueprint.route('/api/types/create', methods=['POST'])
@access_required(permission='documents.upload')
def type_create():
    nom = request.form.get('nom', '').strip()
    if not nom:
        return jsonify({'success': False, 'error': 'Le nom est requis'}), 400
    existing = TypeDocument.query.filter_by(
        entreprise_id=current_user.entreprise_id, nom=nom
    ).first()
    if existing:
        return jsonify({'success': False, 'error': 'Ce type existe deja'}), 400
    td = TypeDocument(
        nom=nom, description=request.form.get('description'),
        entreprise_id=current_user.entreprise_id,
    )
    db.session.add(td)
    db.session.commit()
    return jsonify({'success': True, 'id': td.id})


@blueprint.route('/api/types/<int:type_id>/update', methods=['POST'])
@access_required(permission='documents.upload')
def type_update(type_id):
    td = TypeDocument.query.filter_by(
        id=type_id
    ).first_or_404()
    if request.form.get('nom'):
        td.nom = request.form['nom']
    if request.form.get('description') is not None:
        td.description = request.form['description']
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/types/<int:type_id>/delete', methods=['POST'])
@access_required(permission='documents.archiver')
def type_delete(type_id):
    td = TypeDocument.query.filter_by(
        id=type_id
    ).first_or_404()
    ProofMaster.query.filter_by(type_document_id=type_id).update({'type_document_id': None})
    db.session.delete(td)
    db.session.commit()
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Enhanced search / filter API
# ---------------------------------------------------------------------------

@blueprint.get('/api/recherche')
@access_required(permission='documents.voir')
@blueprint.response(200, ProofMasterSchema(many=True))
def api_recherche():
    """Recherche avancee dans la GED"""
    q = ProofMaster.query.filter_by(entreprise_id=current_user.entreprise_id, statut='ACTIF')

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.filter(or_(
            ProofMaster.nom_fichier.ilike(like),
            ProofMaster.description.ilike(like),
            ProofMaster.numero_document.ilike(like),
            ProofMaster.mots_cles.ilike(like),
            ProofMaster.notes.ilike(like)))

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

    return q.all()


# ---------------------------------------------------------------------------
# Existing routes (keep as-is or enhanced)
# ---------------------------------------------------------------------------

@blueprint.get('/api/liste')
@access_required(permission='documents.voir')
@blueprint.response(200, ProofMasterSchema(many=True))
def api_liste():
    """Liste simple des documents actifs"""
    return ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id, statut='ACTIF'
    ).order_by(ProofMaster.date_creation.desc()).all()


@blueprint.route('/<int:proof_id>/download')
@access_required(permission='documents.voir')
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
@access_required(permission='documents.archiver')
def archiver(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    _log_workflow(proof_id, 'archive', 'Document archivé', current_user.id)
    ProofService.archive_proof(proof.id)
    db.session.commit()
    flash('Document archivé.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/restaurer', methods=['POST'])
@access_required(permission='documents.archiver')
def restaurer(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    proof.statut = 'ACTIF'
    db.session.commit()
    flash('Document restauré.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/supprimer', methods=['POST'])
@access_required(permission='documents.archiver')
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
@access_required(permission='documents.upload')
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
@access_required(permission='documents.voir')
def api_actives():
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id, statut='ACTIF'
    ).order_by(ProofMaster.nom_fichier).all()
    return jsonify([{
        'id': p.id, 'nom_fichier': p.nom_fichier,
        'description': p.description, 'type': p.type,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
    } for p in proofs])
