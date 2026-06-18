import io
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class MinioService:
    """MinIO S3-compatible storage service.

    Used for storing uploaded files (proofs, document PDFs, exports).
    Falls back to local filesystem if MinIO is not configured.
    """

    def __init__(self):
        self.client = None
        self.bucket = None
        self._init_client()

    def _init_client(self):
        try:
            import boto3
            endpoint = current_app.config.get('MINIO_ENDPOINT')
            if not endpoint:
                logger.info("MinIO not configured, using local filesystem")
                return
            self.client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=current_app.config.get('MINIO_ACCESS_KEY', ''),
                aws_secret_access_key=current_app.config.get('MINIO_SECRET_KEY', ''),
                config=boto3.session.Config(signature_version='s3v4'),
            )
            self.bucket = current_app.config.get('MINIO_BUCKET', 'qms-platform')
            self._ensure_bucket()
            logger.info("MinIO client initialized at %s", endpoint)
        except Exception as e:
            logger.warning("MinIO init failed, using local filesystem: %s", e)
            self.client = None

    def _ensure_bucket(self):
        if not self.client:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    @property
    def available(self):
        return self.client is not None

    def upload(self, file_obj, object_key):
        if not self.client:
            from werkzeug.utils import secure_filename
            local_path = current_app.config['UPLOAD_FOLDER'] / object_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            file_obj.save(str(local_path))
            return
        self.client.upload_fileobj(file_obj, self.bucket, object_key)

    def download(self, object_key):
        if not self.client:
            local_path = current_app.config['UPLOAD_FOLDER'] / object_key
            return open(str(local_path), 'rb')
        response = self.client.get_object(Bucket=self.bucket, Key=object_key)
        return response['Body']

    def delete(self, object_key):
        if not self.client:
            local_path = current_app.config['UPLOAD_FOLDER'] / object_key
            if local_path.exists():
                local_path.unlink()
            return
        self.client.delete_object(Bucket=self.bucket, Key=object_key)

    def get_presigned_url(self, object_key, expires_in=3600):
        if not self.client:
            return None
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': object_key},
            ExpiresIn=expires_in
        )

    def upload_file(self, file_path, object_key):
        if not self.client:
            import shutil
            local_path = current_app.config['UPLOAD_FOLDER'] / object_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, str(local_path))
            return
        self.client.upload_file(file_path, self.bucket, object_key)
