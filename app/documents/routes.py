import os
import uuid
from flask import render_template, request, jsonify, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import ProofMaster, ProofReference
from app.documents import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.services.proof_service import ProofService
from datetime import datetime, date
from werkzeug.utils import secure_filename


@blueprint.route('/')
@blueprint.route('/gestion')
@login_required
def gestion():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine,
        statut='ACTIF'
    ).order_by(ProofMaster.date_creation.desc()).all()
    return render_template('documents/gestion.html', proofs=proofs, domaine=domaine)


@blueprint.route('/api/liste')
@login_required
def api_liste():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine,
        statut='ACTIF'
    ).order_by(ProofMaster.date_creation.desc()).all()
    return jsonify([{
        'id': p.id,
        'nom_fichier': p.nom_fichier,
        'type': p.type,
        'taille_bytes': p.taille_bytes,
        'description': p.description,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
        'statut': p.statut,
        'date_creation': p.date_creation.isoformat() if p.date_creation else None,
        'reference_count': p.reference_count or 0,
        'uploader': p.uploader.prenom + ' ' + p.uploader.nom if p.uploader else None,
    } for p in proofs])


@blueprint.route('/upload', methods=['POST'])
@login_required
def upload():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    if 'file' not in request.files:
        flash('Aucun fichier selectionne.', 'danger')
        return redirect(url_for('documents.gestion'))

    file = request.files['file']
    if not file.filename:
        flash('Fichier invalide.', 'danger')
        return redirect(url_for('documents.gestion'))

    original_filename = secure_filename(file.filename)
    ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    stored_name = f"{uuid.uuid4().hex}_{original_filename}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'preuves',
                              str(current_user.entreprise_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    file.save(file_path)

    proof = ProofService.create_or_reuse_proof(
        entreprise_id=current_user.entreprise_id,
        nom_fichier=original_filename,
        file_path=file_path,
        domaine=domaine,
        description=request.form.get('description'),
        validite=datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
        if request.form.get('validite') else None,
        uploaded_by=current_user.id,
        categorie=request.form.get('categorie'),
    )
    db.session.commit()
    flash('Document uploade avec succes.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/detail')
@login_required
def detail(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    refs = ProofReference.query.filter_by(proof_master_id=proof.id).all()
    return render_template('documents/detail.html', proof=proof, refs=refs)


@blueprint.route('/<int:proof_id>/download')
@login_required
def download(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], proof.chemin)
    if not os.path.exists(file_path):
        flash('Fichier introuvable.', 'danger')
        return redirect(url_for('documents.gestion'))
    return send_file(file_path, as_attachment=True, download_name=proof.nom_fichier)


@blueprint.route('/<int:proof_id>/archiver', methods=['POST'])
@login_required
def archiver(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    ProofService.archive_proof(proof.id)
    db.session.commit()
    flash('Document archive.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/supprimer', methods=['POST'])
@login_required
def supprimer(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], proof.chemin)
    if os.path.exists(file_path):
        os.remove(file_path)
    ProofService.hard_delete_proof(proof.id)
    db.session.commit()
    flash('Document supprime.', 'success')
    return redirect(url_for('documents.gestion'))


@blueprint.route('/<int:proof_id>/mettre_a_jour', methods=['POST'])
@login_required
def mettre_a_jour(proof_id):
    proof = tenant_get_or_404(ProofMaster, proof_id)
    proof.description = request.form.get('description', proof.description)
    if request.form.get('validite'):
        proof.validite = datetime.strptime(request.form['validite'], '%Y-%m-%d').date()
    proof.categorie = request.form.get('categorie', proof.categorie)
    db.session.commit()
    flash('Document mis a jour.', 'success')
    return redirect(url_for('documents.detail', proof_id=proof.id))


@blueprint.route('/api/actives')
@login_required
def api_actives():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    proofs = ProofMaster.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine,
        statut='ACTIF'
    ).order_by(ProofMaster.nom_fichier).all()
    return jsonify([{
        'id': p.id,
        'nom_fichier': p.nom_fichier,
        'description': p.description,
        'type': p.type,
        'categorie': p.categorie,
        'validite': p.validite.isoformat() if p.validite else None,
    } for p in proofs])
