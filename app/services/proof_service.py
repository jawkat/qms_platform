# =============================================================================
# QMS Platform — Proof Service (Document Management)
# =============================================================================
"""
Service de gestion des preuves/documents.

Ce module gère :
1. L'upload de fichiers (via StorageService — MINIO ou local)
2. La détection de doublons (hash SHA256)
3. Le versioning des documents
4. L'attachement de preuves à des entités (NC, audits, etc.)
5. L'archivage et la suppression

Architecture :
    ┌─────────────────────────────────────────────┐
    │              ProofService                    │
    │                                              │
    │  ┌──────────────┐     ┌──────────────┐     │
    │  │  ProofMaster │ ←→  │ StorageService│     │
    │  │  (SQLAlchemy)│     │ (MINIO/Local) │     │
    │  └──────────────┘     └──────────────┘     │
    └─────────────────────────────────────────────┘

Convention de clés de stockage :
    {eid}/documents/preuves/{hash[:8]}_{filename}

Auteur : QMS Platform Team
Version : 2.0.0 (MINIO integration)
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, BinaryIO

from flask import current_app
from app import db
from app.models import ProofMaster, ProofReference

logger = logging.getLogger(__name__)


class ProofService:
    """
    Service de gestion des preuves/documents.

    Toutes les opérations de stockage sont déléguées au StorageService
    qui gère automatiquement le fallback MINIO → local filesystem.
    """

    # -------------------------------------------------------------------------
    # Hash computation
    # -------------------------------------------------------------------------

    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """
        Calcule le hash SHA256 d'un fichier.

        Utilisé pour la détection de doublons et l'intégrité des fichiers.

        Args:
            file_path: Chemin absolu du fichier

        Returns:
            Hash SHA256 en hexadecimal (64 caractères)
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def compute_stream_hash(file_obj: BinaryIO) -> str:
        """
        Calcule le hash SHA256 d'un stream fichier.

        Args:
            file_obj: Objet fichier ouVERT en mode 'rb'

        Returns:
            Hash SHA256 en hexadecimal
        """
        sha256 = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(65536), b''):
            sha256.update(chunk)
        file_obj.seek(0)
        return sha256.hexdigest()

    # -------------------------------------------------------------------------
    # Upload avec StorageService
    # -------------------------------------------------------------------------

    @staticmethod
    def create_or_reuse_proof(
        entreprise_id: int,
        nom_fichier: str,
        file_path: str = None,
        file_obj: BinaryIO = None,
        domaine: str = 'hse',
        description: str = None,
        validite=None,
        uploaded_by: int = None,
        categorie: str = None,
    ) -> ProofMaster:
        """
        Crée une nouvelle preuve ou réutilise une existante (détection doublons).

        Si un fichier avec le même hash existe déjà pour cette entreprise,
        la preuve existante est retournée. Sinon, un nouveau ProofMaster
        est créé et le fichier est stocké via StorageService.

        Args:
            entreprise_id: ID de l'entreprise (multi-tenant)
            nom_fichier: Nom original du fichier
            file_path: Chemin local du fichier (si upload depuis disque)
            file_obj: Objet fichier (si upload depuis stream)
            domaine: Domaine ('hse' ou 'qualite')
            description: Description du document
            validite: Date de validité (optionnel)
            uploaded_by: ID de l'utilisateur qui upload
            categorie: Catégorie du document

        Returns:
            Instance ProofMaster (existante ou nouvellement créée)
        """
        from app.core.storage import get_storage

        # Calculer le hash et la taille
        if file_obj:
            file_hash = ProofService.compute_stream_hash(file_obj)
            file_obj.seek(0, 2)  # Seek to end
            taille = file_obj.tell()
            file_obj.seek(0)
        elif file_path:
            file_hash = ProofService.compute_file_hash(file_path)
            taille = os.path.getsize(file_path)
        else:
            raise ValueError("Either file_path or file_obj must be provided")

        ext = os.path.splitext(nom_fichier)[1].lower().lstrip('.')

        # Vérifier les doublons
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
            logger.info("Reusing existing proof %d (duplicate detected)", existing.id)
            return existing

        # Générer la clé de stockage
        from app.core.storage import StorageService
        storage_key = StorageService.generate_key(
            entreprise_id=entreprise_id,
            module='documents',
            categorie='preuves',
            filename=nom_fichier,
        )

        # Stocker le fichier via StorageService
        storage = get_storage()
        if file_obj:
            storage.upload(file_obj, storage_key)
        elif file_path:
            from werkzeug.utils import secure_filename
            import shutil
            # Copier vers un emplacement temporaire pour l'upload
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                shutil.copy2(file_path, tmp.name)
                tmp.seek(0)
                storage.upload(tmp, storage_key)
            os.unlink(tmp.name)

        # Créer le ProofMaster
        proof = ProofMaster(
            entreprise_id=entreprise_id,
            domaine=domaine,
            nom_fichier=nom_fichier,
            type=ext,
            chemin=storage_key,  # Clé de stockage (pas un chemin local)
            taille_bytes=taille,
            hash_fichier=file_hash,
            description=description,
            validite=validite,
            categorie=categorie,
            upload_par=uploaded_by,
            statut='ACTIF',
        )
        db.session.add(proof)
        db.session.flush()

        logger.info(
            "Proof created: %d (%s, %d bytes, key=%s)",
            proof.id, nom_fichier, taille, storage_key
        )
        return proof

    # -------------------------------------------------------------------------
    # Download via StorageService
    # -------------------------------------------------------------------------

    @staticmethod
    def get_proof_stream(proof_id: int):
        """
        Récupère le stream d'un fichier preuve.

        Args:
            proof_id: ID de la preuve

        Returns:
            Objet fichier en mode 'rb', ou None si introuvable
        """
        from app.core.storage import get_storage

        proof = db.session.get(ProofMaster, proof_id)
        if not proof:
            return None

        storage = get_storage()
        return storage.download(proof.chemin)

    @staticmethod
    def get_proof_url(proof_id: int, expires_in: int = 3600) -> Optional[str]:
        """
        Génère une URL signée pour accéder à un fichier.

        Args:
            proof_id: ID de la preuve
            expires_in: Durée de validité en secondes

        Returns:
            URL signée ou None si non supporté
        """
        from app.core.storage import get_storage

        proof = db.session.get(ProofMaster, proof_id)
        if not proof:
            return None

        storage = get_storage()
        return storage.get_presigned_url(proof.chemin, expires_in)

    # -------------------------------------------------------------------------
    # Delete via StorageService
    # -------------------------------------------------------------------------

    @staticmethod
    def delete_proof_file(proof_id: int) -> bool:
        """
        Supprime le fichier associé à une preuve du stockage.

        Args:
            proof_id: ID de la preuve

        Returns:
            True si supprimé avec succès
        """
        from app.core.storage import get_storage

        proof = db.session.get(ProofMaster, proof_id)
        if not proof:
            return False

        storage = get_storage()
        deleted = storage.delete(proof.chemin)
        logger.info("Proof file deleted: %d (key=%s, success=%s)", proof_id, proof.chemin, deleted)
        return deleted

    # -------------------------------------------------------------------------
    # Attach / Detach
    # -------------------------------------------------------------------------

    @staticmethod
    def attach_proof(
        entreprise_id: int,
        entity_type: str,
        entity_id: int,
        proof_id: int,
        attached_by: int = None,
    ) -> ProofReference:
        """
        Attache une preuve à une entité (NC, audit, formation, etc.).

        Args:
            entreprise_id: ID de l'entreprise
            entity_type: Type d'entité ('nonconformite', 'audit', etc.)
            entity_id: ID de l'entité
            proof_id: ID de la preuve
            attached_by: ID de l'utilisateur qui attache

        Returns:
            Instance ProofReference
        """
        existing = ProofReference.query.filter_by(
            proof_master_id=proof_id,
            entity_type=entity_type,
            entity_id=entity_id,
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
    def detach_proof(proof_id: int, entity_type: str, entity_id: int) -> Optional[ProofReference]:
        """
        Détache une preuve d'une entité.

        Args:
            proof_id: ID de la preuve
            entity_type: Type d'entité
            entity_id: ID de l'entité

        Returns:
            ProofReference supprimé ou None
        """
        ref = ProofReference.query.filter_by(
            proof_master_id=proof_id,
            entity_type=entity_type,
            entity_id=entity_id,
        ).first()
        if ref:
            db.session.delete(ref)
            proof = db.session.get(ProofMaster, proof_id)
            if proof and proof.reference_count and proof.reference_count > 0:
                proof.reference_count -= 1
            db.session.flush()
        return ref

    # -------------------------------------------------------------------------
    # Archive / Delete
    # -------------------------------------------------------------------------

    @staticmethod
    def archive_proof(proof_id: int) -> Optional[ProofMaster]:
        """
        Archive une preuve (statut ARCHIVE, fichier conservé).

        Args:
            proof_id: ID de la preuve

        Returns:
            ProofMaster mis à jour
        """
        proof = db.session.get(ProofMaster, proof_id)
        if proof:
            proof.statut = 'ARCHIVE'
            db.session.flush()
        return proof

    @staticmethod
    def hard_delete_proof(proof_id: int) -> Optional[ProofMaster]:
        """
        Supprime définitivement une preuve et son fichier.

        Args:
            proof_id: ID de la preuve

        Returns:
            ProofMaster supprimé ou None
        """
        proof = db.session.get(ProofMaster, proof_id)
        if proof:
            # Supprimer le fichier du stockage
            ProofService.delete_proof_file(proof_id)
            # Supprimer l'enregistrement
            db.session.delete(proof)
            db.session.flush()
        return proof

    # -------------------------------------------------------------------------
    # Versioning
    # -------------------------------------------------------------------------

    @staticmethod
    def replace_proof(old_proof_id: int, new_proof_id: int) -> Optional[ProofMaster]:
        """
        Remplace une preuve par une nouvelle version.

        L'ancienne preuve passe en statut 'REMPLACE' et toutes ses
        références sont transférées à la nouvelle.

        Args:
            old_proof_id: ID de l'ancienne preuve
            new_proof_id: ID de la nouvelle preuve

        Returns:
            Nouvelle ProofMaster
        """
        old = db.session.get(ProofMaster, old_proof_id)
        new_p = db.session.get(ProofMaster, new_proof_id)
        if old and new_p:
            old.statut = 'REMPLACE'
            new_p.remplace_preuve_id = old_proof_id

            # Transférer les références
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
