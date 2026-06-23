import os
import json
import uuid
import tempfile
import pytest
from io import BytesIO
from pathlib import Path

from app import db
from app.models import Dossier, ProofMaster, TypeDocument
from app.services.proof_service import ProofService
from app.core.storage import StorageService, get_storage


# =============================================================================
# Dossier (folder) API tests
# =============================================================================

class TestDossierAPI:
    """Tests for the dossier tree API — ensures no regression on isoformat fix."""

    def test_api_dossiers_requires_login(self, client):
        resp = client.get('/documents/api/dossiers', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_dossiers_returns_valid_json(self, login_client, session, entreprise):
        d1 = Dossier(nom='Folder A', entreprise_id=entreprise.id, domaine='hse')
        d2 = Dossier(nom='Folder B', entreprise_id=entreprise.id, domaine='hse')
        d1a = Dossier(nom='Sub A1', parent_id=1, entreprise_id=entreprise.id, domaine='hse')
        session.add_all([d1, d2, d1a])
        session.commit()

        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert len(data) >= 2
        # Check tree structure — each item has id, nom, date_creation (iso string), children
        for item in data:
            assert 'id' in item
            assert 'nom' in item
            assert 'date_creation' in item
            assert isinstance(item['date_creation'], str)
            assert 'date_modification' in item
            assert isinstance(item['date_modification'], str)
            assert 'children' in item
            assert 'doc_count' in item

    def test_api_dossiers_hierarchy(self, login_client, session, entreprise):
        parent = Dossier(nom='Parent', entreprise_id=entreprise.id, domaine='hse')
        session.add(parent)
        session.flush()
        child = Dossier(nom='Child', parent_id=parent.id, entreprise_id=entreprise.id, domaine='hse')
        session.add(child)
        session.flush()
        grandchild = Dossier(nom='Grandchild', parent_id=child.id, entreprise_id=entreprise.id, domaine='hse')
        session.add(grandchild)
        session.commit()

        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        parent_item = next(d for d in data if d['nom'] == 'Parent')
        assert len(parent_item['children']) == 1
        assert parent_item['children'][0]['nom'] == 'Child'
        assert parent_item['children'][0]['children'][0]['nom'] == 'Grandchild'

    def test_api_dossiers_doc_count(self, login_client, session, entreprise, manager_user):
        dossier = Dossier(nom='Docs', entreprise_id=entreprise.id, domaine='hse')
        session.add(dossier)
        session.flush()
        for i in range(3):
            p = ProofMaster(
                entreprise_id=entreprise.id, domaine='hse',
                nom_fichier=f'doc{i}.pdf', chemin=f'path/doc{i}.pdf',
                statut='ACTIF', dossier_id=dossier.id, upload_par=manager_user.id,
            )
            session.add(p)
        session.commit()

        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        item = next(d for d in data if d['nom'] == 'Docs')
        assert item['doc_count'] == 3

    def test_api_dossiers_scoped_by_entreprise(self, login_client, session, entreprise):
        d1 = Dossier(nom='Visible', entreprise_id=entreprise.id, domaine='hse')
        session.add(d1)
        session.flush()
        # Create a second entreprise
        from app.models import Entreprise
        other = Entreprise(nom='Other Corp', modules_actifs=['ged'], statut='active')
        session.add(other)
        session.flush()
        d2 = Dossier(nom='Hidden', entreprise_id=other.id, domaine='hse')
        session.add(d2)
        session.commit()

        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        names = [d['nom'] for d in data]
        assert 'Visible' in names
        assert 'Hidden' not in names

    def test_api_dossiers_scoped_by_domaine(self, login_client, session, entreprise):
        d_hse = Dossier(nom='HSE Doc', entreprise_id=entreprise.id, domaine='hse')
        d_qualite = Dossier(nom='Qualite Doc', entreprise_id=entreprise.id, domaine='qualite')
        session.add_all([d_hse, d_qualite])
        session.commit()

        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        names = [d['nom'] for d in data]
        assert 'HSE Doc' in names
        assert 'Qualite Doc' not in names


class TestDossierCRUD:
    """Dossier creation, rename, delete, move."""

    def test_create_dossier(self, login_client, session, entreprise):
        resp = login_client.post('/documents/api/dossiers/create', data={
            'nom': 'New Folder',
        }, follow_redirects=True)
        assert resp.status_code == 200
        q = Dossier.query.filter_by(nom='New Folder', entreprise_id=entreprise.id)
        assert q.count() == 1

    def test_create_nested_dossier(self, login_client, session, entreprise):
        parent = Dossier(nom='Parent', entreprise_id=entreprise.id, domaine='hse')
        session.add(parent)
        session.commit()

        resp = login_client.post('/documents/api/dossiers/create', data={
            'nom': 'Child',
            'parent_id': parent.id,
        }, follow_redirects=True)
        assert resp.status_code == 200
        child = Dossier.query.filter_by(nom='Child', entreprise_id=entreprise.id).first()
        assert child is not None
        assert child.parent_id == parent.id

    def test_create_dossier_empty_name(self, login_client):
        resp = login_client.post('/documents/api/dossiers/create', data={
            'nom': '',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'nom du dossier est requis' in resp.data

    def test_rename_dossier(self, login_client, session, entreprise):
        d = Dossier(nom='Old Name', entreprise_id=entreprise.id, domaine='hse')
        session.add(d)
        session.commit()

        resp = login_client.post(f'/documents/api/dossiers/{d.id}/rename', data={
            'nom': 'New Name',
        }, follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(d)
        assert d.nom == 'New Name'

    def test_delete_dossier(self, login_client, session, entreprise):
        d = Dossier(nom='To Delete', entreprise_id=entreprise.id, domaine='hse')
        session.add(d)
        session.commit()
        did = d.id

        resp = login_client.post(f'/documents/api/dossiers/{did}/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Dossier, did) is None

    def test_delete_dossier_with_children(self, login_client, session, entreprise):
        parent = Dossier(nom='Parent', entreprise_id=entreprise.id, domaine='hse')
        session.add(parent)
        session.flush()
        child = Dossier(nom='Child', parent_id=parent.id, entreprise_id=entreprise.id, domaine='hse')
        session.add(child)
        session.commit()

        resp = login_client.post(f'/documents/api/dossiers/{parent.id}/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Dossier, parent.id) is None
        # Children survive but with parent_id set to NULL
        surviving_child = db.session.get(Dossier, child.id)
        assert surviving_child is not None
        assert surviving_child.parent_id is None

    def test_api_types_returns_list(self, login_client, session, entreprise):
        td = TypeDocument(nom='Rapport', description='Test', entreprise_id=entreprise.id, domaine='hse')
        session.add(td)
        session.commit()

        resp = login_client.get('/documents/api/types')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert isinstance(data, list)
        assert any(t['nom'] == 'Rapport' for t in data)


# =============================================================================
# Document download tests
# =============================================================================

class TestDocumentDownload:
    """Tests for the document download endpoint."""

    def test_download_requires_login(self, client, proof):
        resp = client.get(f'/documents/{proof.id}/download', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_download_local_fs_file(self, login_client, session, entreprise, app, manager_user):
        upload_dir = app.config['UPLOAD_FOLDER']
        content = b'hello world this is a test file'
        filename = 'test_document.pdf'
        relative_dir = f'{entreprise.id}/preuves'
        os.makedirs(os.path.join(upload_dir, relative_dir), exist_ok=True)
        file_path = os.path.join(upload_dir, relative_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)

        proof = ProofMaster(
            entreprise_id=entreprise.id, domaine='hse',
            nom_fichier='test_document.pdf', type='pdf',
            chemin=f'{entreprise.id}/preuves/{filename}',
            taille_bytes=len(content), statut='ACTIF',
            upload_par=manager_user.id,
        )
        session.add(proof)
        session.commit()

        resp = login_client.get(f'/documents/{proof.id}/download')
        assert resp.status_code == 200
        assert resp.data == content
        assert 'test_document.pdf' in resp.headers.get('Content-Disposition', '')

    def test_download_legacy_proof_no_extension(self, login_client, session, entreprise, app, manager_user):
        upload_dir = app.config['UPLOAD_FOLDER']
        content = b'legacy file content'
        filename = 'legacy_file.txt'
        relative_dir = f'{entreprise.id}/preuves'
        os.makedirs(os.path.join(upload_dir, relative_dir), exist_ok=True)
        file_path = os.path.join(upload_dir, relative_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)

        proof = ProofMaster(
            entreprise_id=entreprise.id, domaine='hse',
            nom_fichier='legacy_label', type='preuve_veille',
            chemin=f'{entreprise.id}/preuves/{filename}',
            taille_bytes=len(content), statut='ACTIF',
            upload_par=manager_user.id,
        )
        session.add(proof)
        session.commit()

        resp = login_client.get(f'/documents/{proof.id}/download')
        assert resp.status_code == 200
        assert resp.data == content
        disp = resp.headers.get('Content-Disposition', '')
        assert filename in disp

    def test_download_nonexistent_proof(self, login_client):
        resp = login_client.get('/documents/99999/download', follow_redirects=True)
        assert resp.status_code in (302, 404, 200)
        # 302 = redirect to gestion with flash, 404 = tenant_get_or_404

    def test_download_from_storage_service(self, login_client, session, entreprise, app, manager_user):
        with app.app_context():
            storage = get_storage()
            content = b'stored via storage service'
            file_obj = BytesIO(content)
            storage_key = f'{entreprise.id}/documents/preuves/test_storage_file.bin'
            storage.upload(file_obj, storage_key)

        proof = ProofMaster(
            entreprise_id=entreprise.id, domaine='hse',
            nom_fichier='test_storage_file.bin', type='bin',
            chemin=storage_key,
            taille_bytes=len(content), statut='ACTIF',
            upload_par=manager_user.id,
        )
        session.add(proof)
        session.commit()

        resp = login_client.get(f'/documents/{proof.id}/download')
        assert resp.status_code == 200
        assert resp.data == content


# =============================================================================
# StorageService (local FS fallback) tests
# =============================================================================

class TestStorageServiceLocalFS:
    """Tests for StorageService with local filesystem backend."""

    def test_upload_download(self, app):
        with app.app_context():
            storage = get_storage()
            content = b'storage service test content'
            key = '1/test/uploaded_file.txt'
            file_obj = BytesIO(content)
            result = storage.upload(file_obj, key)
            assert result['object_key'] == key
            assert result['size'] == len(content)

            stream = storage.download(key)
            assert stream is not None
            assert stream.read() == content

    def test_download_nonexistent(self, app):
        with app.app_context():
            storage = get_storage()
            stream = storage.download('nonexistent/key.txt')
            assert stream is None

    def test_delete_file(self, app):
        with app.app_context():
            storage = get_storage()
            key = '1/test/to_delete.txt'
            storage.upload(BytesIO(b'delete me'), key)
            assert storage.exists(key) is True
            result = storage.delete(key)
            assert result is True
            assert storage.exists(key) is False

    def test_delete_nonexistent(self, app):
        with app.app_context():
            storage = get_storage()
            # MinIO returns True even for nonexistent keys; local FS returns False
            result = storage.delete(f'nonexistent/{uuid.uuid4().hex}.txt')
            assert result is not None

    def test_exists(self, app):
        with app.app_context():
            storage = get_storage()
            key = f'1/test/exists_check_{uuid.uuid4().hex}.txt'
            assert storage.exists(key) is False
            storage.upload(BytesIO(b'check'), key)
            assert storage.exists(key) is True

    def test_get_info(self, app):
        with app.app_context():
            storage = get_storage()
            key = '1/test/info_file.txt'
            storage.upload(BytesIO(b'info content'), key)
            info = storage.get_info(key)
            assert info is not None
            assert 'size' in info
            assert info['size'] == 12
            assert 'last_modified' in info

    def test_get_info_nonexistent(self, app):
        with app.app_context():
            storage = get_storage()
            info = storage.get_info('nonexistent/key.txt')
            assert info is None

    def test_get_presigned_url_local_fs(self, app):
        with app.app_context():
            storage = get_storage()
            key = f'some/presigned_{uuid.uuid4().hex}.txt'
            url = storage.get_presigned_url(key)
            # MinIO returns a signed URL; local FS returns None
            if storage._client is None:
                assert url is None
            else:
                assert url is not None
                assert url.startswith('http')

    def test_generate_key(self, app):
        with app.app_context():
            key = StorageService.generate_key(
                entreprise_id=42, module='documents',
                categorie='preuves', filename='rapport.pdf'
            )
            assert key.startswith('42/documents/preuves/')
            assert key.endswith('_rapport.pdf')

    def test_generate_doc_key(self, app):
        with app.app_context():
            key = StorageService.generate_doc_key(entreprise_id=5, filename='doc.pdf', version=2)
            assert key.startswith('5/documents/v2_')
            assert key.endswith('_doc.pdf')

    def test_generate_haccp_key(self, app):
        with app.app_context():
            key = StorageService.generate_haccp_key(entreprise_id=3, categorie='ccp', filename='data.csv')
            assert key.startswith('3/haccp/ccp/')
            assert key.endswith('_data.csv')

    def test_minio_fallback_on_missing_endpoint(self, app):
        with app.app_context():
            old_endpoint = app.config.get('MINIO_ENDPOINT')
            app.config['MINIO_ENDPOINT'] = 'http://nonexistent:9999'
            try:
                storage = StorageService()
                assert storage._client is None
                assert storage._local_root is not None
                content = b'fallback works'
                key = 'fallback/test.txt'
                storage.upload(BytesIO(content), key)
                stream = storage.download(key)
                assert stream is not None
                assert stream.read() == content
            finally:
                app.config['MINIO_ENDPOINT'] = old_endpoint

    def test_upload_with_content_type(self, app):
        with app.app_context():
            storage = get_storage()
            key = '1/test/meta_test.txt'
            storage.upload(BytesIO(b'content type test'), key, content_type='text/plain')
            assert storage.exists(key) is True

    def test_large_file_upload_download(self, app):
        with app.app_context():
            storage = get_storage()
            content = b'x' * 100_000
            key = '1/test/large_file.bin'
            storage.upload(BytesIO(content), key)
            stream = storage.download(key)
            assert stream is not None
            assert len(stream.read()) == 100_000

    def test_storage_singleton(self, app):
        with app.app_context():
            s1 = get_storage()
            s2 = get_storage()
            assert s1 is s2


# =============================================================================
# ProofService.get_proof_stream() tests
# =============================================================================

class TestProofServiceGetProofStream:
    """Tests for ProofService.get_proof_stream() — used by download route."""

    def test_get_stream_nonexistent_proof(self, app, session):
        with app.app_context():
            stream = ProofService.get_proof_stream(99999)
            assert stream is None

    def test_get_stream_storage_key(self, app, session, entreprise):
        with app.app_context():
            storage = get_storage()
            content = b'stream test content'
            key = f'{entreprise.id}/documents/preuves/stream_test.txt'
            storage.upload(BytesIO(content), key)

            proof = ProofMaster(
                entreprise_id=entreprise.id, domaine='hse',
                nom_fichier='stream_test.txt', type='txt',
                chemin=key, taille_bytes=len(content),
                statut='ACTIF',
            )
            session.add(proof)
            session.commit()

            stream = ProofService.get_proof_stream(proof.id)
            assert stream is not None
            assert stream.read() == content

    def test_get_stream_legacy_path(self, app, session, entreprise):
        with app.app_context():
            storage = get_storage()
            content = b'legacy path test'
            key = f'{entreprise.id}/documents/preuves/legacy_test.txt'
            storage.upload(BytesIO(content), key)

            proof = ProofMaster(
                entreprise_id=entreprise.id, domaine='hse',
                nom_fichier='legacy_test.txt', type='txt',
                chemin='legacy_test.txt',  # no '/' — triggers fallback
                taille_bytes=len(content), statut='ACTIF',
            )
            session.add(proof)
            session.commit()

            stream = ProofService.get_proof_stream(proof.id)
            assert stream is not None
            assert stream.read() == content

    def test_get_stream_local_fs_fallback(self, app, session, entreprise):
        with app.app_context():
            storage = get_storage()
            content = b'local fs fallback for stream'
            key = f'{entreprise.id}/documents/preuves/fs_fallback.txt'
            storage.upload(BytesIO(content), key)

            proof = ProofMaster(
                entreprise_id=entreprise.id, domaine='hse',
                nom_fichier='fs_fallback.txt', type='txt',
                chemin=key, taille_bytes=len(content),
                statut='ACTIF',
            )
            session.add(proof)
            session.commit()

            stream = ProofService.get_proof_stream(proof.id)
            assert stream is not None
            assert stream.read() == content

    def test_get_stream_legacy_path_via_storage(self, app, session, entreprise):
        """chemin without '/' triggers the legacy lookup fallback in get_proof_stream."""
        with app.app_context():
            storage = get_storage()
            content = b'legacy path via storage test'
            filename = 'legacy_via_storage.txt'
            full_key = f'{entreprise.id}/documents/preuves/{filename}'
            storage.upload(BytesIO(content), full_key)

            proof = ProofMaster(
                entreprise_id=entreprise.id, domaine='hse',
                nom_fichier='legacy_name_via_storage', type='txt',
                chemin=filename,  # no '/' — triggers legacy fallback in stream
                taille_bytes=len(content), statut='ACTIF',
            )
            session.add(proof)
            session.commit()

            stream = ProofService.get_proof_stream(proof.id)
            assert stream is not None
            assert stream.read() == content
