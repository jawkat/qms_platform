# =============================================================================
# QMS Platform — Unified Storage Layer
# =============================================================================
"""
Couche de stockage unifiée pour la gestion des fichiers.

Ce module fournit une interface unique pour le stockage de fichiers,
avec support MINIO (S3-compatible) en production et filesystem local
en développement.

Architecture :
    ┌─────────────────────────────────────────────┐
    │              StorageService                  │
    │                                              │
    │  ┌──────────┐        ┌──────────┐           │
    │  │  MINIO   │ ←──→   │  Local   │           │
    │  │  (S3)    │        │  FS      │           │
    │  └──────────┘        └──────────┘           │
    │       ↑                    ↑                 │
    │  Production          Development             │
    └─────────────────────────────────────────────┘

Les chemins de stockage suivent la convention :
    {bucket}/{entreprise_id}/{module}/{categorie}/{filename}

Exemple :
    qms-platform/1/documents/preuves/abc123_rapport.pdf
    qms-platform/1/haccp/enregistrements/ccp01_2024-01-15.csv

Auteur : QMS Platform Team
Version : 1.0.0
"""

import os
import uuid
import hashlib
import logging
from typing import Optional, BinaryIO, Dict, Tuple
from datetime import datetime
from pathlib import Path

from flask import current_app

logger = logging.getLogger(__name__)


# =============================================================================
# Storage Service — Interface unifiée
# =============================================================================

class StorageService:
    """
    Service de stockage unifié avec fallback automatique.

    Utilise MINIO quand il est configuré, sinon le filesystem local.
    Toutes les opérations suivent la même interface quelle que soit
    le backend de stockage.

    Exemple :
        storage = StorageService()
        storage.upload(file_obj, 'documents/rapport.pdf')
        content = storage.download('documents/rapport.pdf')
        storage.delete('documents/rapport.pdf')
    """

    def __init__(self):
        """Initialise le client de stockage."""
        self._client = None
        self._bucket = None
        self._local_root = None
        self._init_backend()

    def _init_backend(self):
        """
        Initialise le backend de stockage.

        Tente d'abord MINIO, puis fallback sur le filesystem local.
        """
        # Essayer MINIO
        try:
            endpoint = current_app.config.get('MINIO_ENDPOINT')
            if endpoint:
                import boto3
                self._client = boto3.client(
                    's3',
                    endpoint_url=endpoint,
                    region_name='us-east-1',
                    aws_access_key_id=current_app.config.get('MINIO_ACCESS_KEY', ''),
                    aws_secret_access_key=current_app.config.get('MINIO_SECRET_KEY', ''),
                    config=boto3.session.Config(
                        signature_version='s3v4',
                        s3={'addressing_style': 'path'},
                    ),
                )
                self._bucket = current_app.config.get('MINIO_BUCKET', 'qms-platform')
                self._ensure_bucket()
                logger.info("MINIO storage initialized at %s", endpoint)
                return
        except Exception as e:
            logger.warning("MINIO init failed, falling back to local FS: %s", e)
            self._client = None

        # Fallback filesystem local
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        self._local_root = Path(upload_folder)
        self._local_root.mkdir(parents=True, exist_ok=True)
        logger.info("Local filesystem storage initialized at %s", self._local_root)

    def _ensure_bucket(self):
        """Crée le bucket MINIO s'il n'existe pas."""
        if not self._client:
            return
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except Exception:
            self._client.create_bucket(Bucket=self._bucket)
            logger.info("Created MINIO bucket: %s", self._bucket)

    # -------------------------------------------------------------------------
    # Opérations CRUD
    # -------------------------------------------------------------------------

    def upload(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Upload un fichier vers le stockage.

        Args:
            file_obj: Objet fichier (ouVERT en mode 'rb')
            object_key: Chemin clé dans le stockage
                         (ex: '1/documents/preuves/abc.pdf')
            content_type: Type MIME du fichier (optionnel)
            metadata: Métadonnées supplémentaires (optionnel)

        Returns:
            Dict avec les informations du fichier uploadé :
            - object_key: Clé de stockage
            - size: Taille en bytes
            - hash: SHA256 du fichier
            - uploaded_at: Timestamp de l'upload
        """
        # Calculer le hash du fichier
        content = file_obj.read()
        file_hash = hashlib.sha256(content).hexdigest()
        file_obj.seek(0)

        size = len(content)

        if self._client:
            # Upload vers MINIO
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata

            self._client.upload_fileobj(
                file_obj, self._bucket, object_key,
                ExtraArgs=extra_args if extra_args else None
            )
            logger.info("Uploaded to MINIO: %s (%d bytes)", object_key, size)
        else:
            # Upload vers filesystem local
            local_path = self._local_root / object_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(content)
            logger.info("Uploaded to local FS: %s (%d bytes)", object_key, size)

        return {
            'object_key': object_key,
            'size': size,
            'hash': file_hash,
            'uploaded_at': datetime.utcnow().isoformat(),
        }

    def download(self, object_key: str) -> Optional[BinaryIO]:
        """
        Télécharge un fichier du stockage.

        Args:
            object_key: Clé du fichier à télécharger

        Returns:
            Objet fichier en mode 'rb', ou None si introuvable
        """
        if self._client:
            try:
                response = self._client.get_object(Bucket=self._bucket, Key=object_key)
                return response['Body']
            except Exception as e:
                logger.error("MINIO download failed for %s: %s", object_key, e)
                return None
        else:
            local_path = self._local_root / object_key
            if local_path.exists():
                return open(local_path, 'rb')
            logger.warning("File not found: %s", object_key)
            return None

    def delete(self, object_key: str) -> bool:
        """
        Supprime un fichier du stockage.

        Args:
            object_key: Clé du fichier à supprimer

        Returns:
            True si supprimé, False si introuvable
        """
        if self._client:
            try:
                self._client.delete_object(Bucket=self._bucket, Key=object_key)
                logger.info("Deleted from MINIO: %s", object_key)
                return True
            except Exception as e:
                logger.error("MINIO delete failed for %s: %s", object_key, e)
                return False
        else:
            local_path = self._local_root / object_key
            if local_path.exists():
                local_path.unlink()
                logger.info("Deleted from local FS: %s", object_key)
                return True
            return False

    def exists(self, object_key: str) -> bool:
        """
        Vérifie si un fichier existe dans le stockage.

        Args:
            object_key: Clé du fichier

        Returns:
            True si le fichier existe
        """
        if self._client:
            try:
                self._client.head_object(Bucket=self._bucket, Key=object_key)
                return True
            except Exception:
                return False
        else:
            return (self._local_root / object_key).exists()

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Génère une URL signée pour accéder à un fichier.

        Utile pour les téléchargements temporaires ou les preview.

        Args:
            object_key: Clé du fichier
            expires_in: Durée de validité en secondes (défaut: 1h)

        Returns:
            URL signée ou None si non supporté
        """
        if self._client:
            return self._client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self._bucket, 'Key': object_key},
                ExpiresIn=expires_in
            )
        return None  # Non supporté en local

    def get_info(self, object_key: str) -> Optional[Dict]:
        """
        Récupère les métadonnées d'un fichier.

        Args:
            object_key: Clé du fichier

        Returns:
            Dict avec size, content_type, last_modified, etc.
        """
        if self._client:
            try:
                response = self._client.head_object(Bucket=self._bucket, Key=object_key)
                return {
                    'size': response.get('ContentLength', 0),
                    'content_type': response.get('ContentType', ''),
                    'last_modified': response.get('LastModified', '').isoformat(),
                    'etag': response.get('ETag', ''),
                }
            except Exception:
                return None
        else:
            local_path = self._local_root / object_key
            if local_path.exists():
                stat = local_path.stat()
                return {
                    'size': stat.st_size,
                    'content_type': '',
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'etag': '',
                }
            return None

    # -------------------------------------------------------------------------
    # Génération de clés de stockage
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_key(
        entreprise_id: int,
        module: str,
        categorie: str,
        filename: str,
        prefix: str = None
    ) -> str:
        """
        Génère une clé de stockage unique pour un fichier.

        Format : {entreprise_id}/{module}/{categorie}/{uuid}_{filename}
        Exemple : 1/documents/preuves/a1b2c3_rapport.pdf

        Args:
            entreprise_id: ID de l'entreprise (multi-tenant)
            module: Module source ('documents', 'haccp', 'hse', etc.)
            categorie: Catégorie du fichier ('preuves', 'enregistrements', etc.)
            filename: Nom original du fichier
            prefix: Préfixe optionnel (ex: date '2024-01')

        Returns:
            Clé de stockage unique
        """
        safe_filename = uuid.uuid4().hex[:8] + '_' + filename
        parts = [str(entreprise_id), module, categorie]
        if prefix:
            parts.append(prefix)
        parts.append(safe_filename)
        return '/'.join(parts)

    @staticmethod
    def generate_doc_key(entreprise_id: int, filename: str, version: int = 1) -> str:
        """
        Génère une clé pour un document GED.

        Format : {eid}/documents/{version}_{uuid}_{filename}

        Args:
            entreprise_id: ID de l'entreprise
            filename: Nom du fichier
            version: Numéro de version

        Returns:
            Clé de stockage
        """
        safe = uuid.uuid4().hex[:8] + '_' + filename
        return f"{entreprise_id}/documents/v{version}_{safe}"

    @staticmethod
    def generate_haccp_key(entreprise_id: int, categorie: str, filename: str) -> str:
        """
        Génère une clé pour un fichier HACCP.

        Args:
            entreprise_id: ID de l'entreprise
            categorie: Sous-catégorie HACCP ('ccp', 'tracabilite', etc.)
            filename: Nom du fichier

        Returns:
            Clé de stockage
        """
        safe = uuid.uuid4().hex[:8] + '_' + filename
        return f"{entreprise_id}/haccp/{categorie}/{safe}"


# =============================================================================
# Instance globale
# =============================================================================

_storage_service = None


def get_storage() -> StorageService:
    """
    Retourne l'instance singleton du StorageService.

    Lazy initialization : le service est créé au premier appel.
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
