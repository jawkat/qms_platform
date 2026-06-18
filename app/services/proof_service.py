import os
import hashlib
import logging
from datetime import datetime
from app import db
from app.models import ProofMaster, ProofReference

logger = logging.getLogger(__name__)


class ProofService:

    @staticmethod
    def compute_file_hash(file_path):
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def create_or_reuse_proof(entreprise_id, nom_fichier, file_path, domaine='hse',
                              description=None, validite=None, uploaded_by=None,
                              categorie=None):
        file_hash = ProofService.compute_file_hash(file_path)
        taille = os.path.getsize(file_path)
        ext = os.path.splitext(nom_fichier)[1].lower().lstrip('.')

        existing = ProofMaster.query.filter_by(
            entreprise_id=entreprise_id,
            hash_fichier=file_hash,
            statut='ACTIF'
        ).first()
        if existing:
            existing.taille_bytes = taille
            existing.nom_fichier = nom_fichier
            existing.date_modification = datetime.utcnow()
            db.session.flush()
            return existing

        from werkzeug.utils import secure_filename
        safe_name = secure_filename(nom_fichier)
        rel_path = f"preuves/{entreprise_id}/{file_hash[:8]}_{safe_name}"

        proof = ProofMaster(
            entreprise_id=entreprise_id,
            domaine=domaine,
            nom_fichier=nom_fichier,
            type=ext,
            chemin=rel_path,
            taille_bytes=taille,
            hash_fichier=file_hash,
            description=description,
            validite=validite,
            categorie=categorie,
            upload_par=uploaded_by,
            statut='ACTIF'
        )
        db.session.add(proof)
        db.session.flush()

        from flask import current_app
        upload_root = current_app.config['UPLOAD_FOLDER'] if current_app else '/tmp'
        dest = os.path.join(upload_root, rel_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        import shutil
        shutil.copy2(file_path, dest)

        return proof

    @staticmethod
    def attach_proof(entreprise_id, entity_type, entity_id, proof_id, attached_by=None):
        existing = ProofReference.query.filter_by(
            proof_master_id=proof_id,
            entity_type=entity_type,
            entity_id=entity_id
        ).first()
        if existing:
            return existing

        ref = ProofReference(
            proof_master_id=proof_id,
            entity_type=entity_type,
            entity_id=entity_id,
            attached_by=attached_by,
        )
        db.session.add(ref)

        proof = db.session.get(ProofMaster, proof_id)
        if proof:
            proof.reference_count = (proof.reference_count or 0) + 1
        db.session.flush()
        return ref

    @staticmethod
    def detach_proof(proof_id, entity_type, entity_id):
        ref = ProofReference.query.filter_by(
            proof_master_id=proof_id,
            entity_type=entity_type,
            entity_id=entity_id
        ).first()
        if ref:
            db.session.delete(ref)
            proof = db.session.get(ProofMaster, proof_id)
            if proof and proof.reference_count and proof.reference_count > 0:
                proof.reference_count -= 1
            db.session.flush()
        return ref

    @staticmethod
    def archive_proof(proof_id):
        proof = db.session.get(ProofMaster, proof_id)
        if proof:
            proof.statut = 'ARCHIVE'
            db.session.flush()
        return proof

    @staticmethod
    def hard_delete_proof(proof_id):
        proof = db.session.get(ProofMaster, proof_id)
        if proof:
            db.session.delete(proof)
            db.session.flush()
        return proof

    @staticmethod
    def replace_proof(old_proof_id, new_proof_id):
        old = db.session.get(ProofMaster, old_proof_id)
        new_p = db.session.get(ProofMaster, new_proof_id)
        if old and new_p:
            old.statut = 'REMPLACE'
            new_p.remplace_preuve_id = old_proof_id
            refs = ProofReference.query.filter_by(proof_master_id=old_proof_id).all()
            for ref in refs:
                new_ref = ProofReference(
                    proof_master_id=new_proof_id,
                    entity_type=ref.entity_type,
                    entity_id=ref.entity_id,
                    attached_by=ref.attached_by,
                )
                db.session.add(new_ref)
                db.session.delete(ref)
            db.session.flush()
        return new_p
