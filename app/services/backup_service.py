import os
import subprocess
import shutil
from datetime import datetime
from flask import current_app
from urllib.parse import urlparse

class BackupService:
    def __init__(self, backup_dir=None):
        self.backup_dir = backup_dir or os.path.join(current_app.root_path, '..', 'backups')
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def _get_db_config(self):
        db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
        if db_url.startswith('sqlite'):
            return {'type': 'sqlite', 'path': db_url.replace('sqlite:///', '')}
        
        parsed = urlparse(db_url)
        return {
            'type': 'postgres',
            'username': parsed.username,
            'password': parsed.password,
            'hostname': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/')
        }

    def create_backup(self):
        """Crée une archive complète (SQL + Uploads)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = os.path.join(self.backup_dir, f'temp_backup_{timestamp}')
        os.makedirs(temp_dir)

        try:
            db_config = self._get_db_config()
            sql_file = os.path.join(temp_dir, 'database.sql')

            if db_config['type'] == 'postgres':
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                cmd = [
                    'pg_dump',
                    '-h', db_config['hostname'],
                    '-p', str(db_config['port']),
                    '-U', db_config['username'],
                    '-f', sql_file,
                    db_config['database']
                ]
                subprocess.run(cmd, env=env, check=True)
            elif db_config['type'] == 'sqlite':
                shutil.copy2(db_config['path'], sql_file)

            # Copier les uploads
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            if os.path.exists(uploads_dir):
                shutil.copytree(uploads_dir, os.path.join(temp_dir, 'uploads'))

            # Créer l'archive
            archive_name = f'backup_{timestamp}'
            archive_path = os.path.join(self.backup_dir, archive_name)
            shutil.make_archive(archive_path, 'zip', temp_dir)
            
            return f'{archive_name}.zip'
        finally:
            shutil.rmtree(temp_dir)

    def list_backups(self):
        """Liste les fichiers de sauvegarde disponibles"""
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip'):
                path = os.path.join(self.backup_dir, filename)
                stats = os.stat(path)
                backups.append({
                    'filename': filename,
                    'size': stats.st_size,
                    'date': datetime.fromtimestamp(stats.st_mtime)
                })
        return sorted(backups, key=lambda x: x['date'], reverse=True)

    def delete_backup(self, filename):
        """Supprime un fichier de sauvegarde"""
        path = os.path.join(self.backup_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def restore_backup(self, filename):
        """Restaure les données depuis une archive"""
        archive_path = os.path.join(self.backup_dir, filename)
        if not os.path.exists(archive_path):
            raise FileNotFoundError("Archive introuvable")

        temp_extract_dir = os.path.join(self.backup_dir, 'temp_restore')
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        os.makedirs(temp_extract_dir)

        try:
            shutil.unpack_archive(archive_path, temp_extract_dir, 'zip')
            
            # 1. Restaurer la base de données
            db_config = self._get_db_config()
            sql_file = os.path.join(temp_extract_dir, 'database.sql')
            
            if db_config['type'] == 'postgres':
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['password']
                cmd = [
                    'psql',
                    '-h', db_config['hostname'],
                    '-p', str(db_config['port']),
                    '-U', db_config['username'],
                    '-d', db_config['database'],
                    '-f', sql_file
                ]
                subprocess.run(cmd, env=env, check=True)
            elif db_config['type'] == 'sqlite':
                shutil.copy2(sql_file, db_config['path'])

            # 2. Restaurer les uploads
            temp_uploads = os.path.join(temp_extract_dir, 'uploads')
            if os.path.exists(temp_uploads):
                uploads_dir = current_app.config['UPLOAD_FOLDER']
                if os.path.exists(uploads_dir):
                    shutil.rmtree(uploads_dir)
                shutil.copytree(temp_uploads, uploads_dir)

            return True
        finally:
            shutil.rmtree(temp_extract_dir)

def run_backup_task():
    """Fonction wrapper pour le worker RQ"""
    from app.services.backup_service import BackupService
    service = BackupService()
    return service.create_backup()

def run_restore_task(filename):
    """Fonction wrapper pour le worker RQ"""
    from app.services.backup_service import BackupService
    service = BackupService()
    return service.restore_backup(filename)
