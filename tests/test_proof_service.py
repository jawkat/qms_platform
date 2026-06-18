import os
import tempfile
import pytest
from app import db
from app.models import ProofMaster, ProofReference
from app.services.proof_service import ProofService


class TestProofServiceComputeHash:
    def test_hash_file(self, app):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'hello world')
            f.flush()
            path = f.name
        try:
            h = ProofService.compute_file_hash(path)
            assert len(h) == 64
            assert isinstance(h, str)
        finally:
            os.unlink(path)

    def test_same_content_same_hash(self, app):
        files = []
        for _ in range(2):
            f = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
            f.write(b'same content')
            f.flush()
            files.append(f.name)
        try:
            assert ProofService.compute_file_hash(files[0]) == ProofService.compute_file_hash(files[1])
        finally:
            for p in files:
                os.unlink(p)


class TestProofServiceAttachDetach:
    def test_attach_proof(self, app, session, entreprise, proof, manager_user):
        with app.app_context():
            ref = ProofService.attach_proof(
                entreprise.id, 'evaluation_article', 1, proof.id, manager_user.id
            )
            session.commit()
            assert ref.id is not None
            assert ref.entity_type == 'evaluation_article'
            assert ref.entity_id == 1

    def test_attach_duplicate_returns_existing(self, app, session, entreprise, proof, manager_user):
        with app.app_context():
            ref1 = ProofService.attach_proof(
                entreprise.id, 'evaluation_article', 1, proof.id, manager_user.id
            )
            session.commit()
            ref2 = ProofService.attach_proof(
                entreprise.id, 'evaluation_article', 1, proof.id, manager_user.id
            )
            session.commit()
            assert ref1.id == ref2.id

    def test_detach_proof(self, app, session, entreprise, proof, manager_user):
        with app.app_context():
            ProofService.attach_proof(
                entreprise.id, 'action_corrective', 5, proof.id, manager_user.id
            )
            session.commit()
            ref = ProofService.detach_proof(proof.id, 'action_corrective', 5)
            session.commit()
            assert ref is not None

    def test_detach_nonexistent_returns_none(self, app, session, proof):
        with app.app_context():
            ref = ProofService.detach_proof(proof.id, 'nonexistent', 999)
            assert ref is None


class TestProofServiceArchive:
    def test_archive_proof(self, app, session, proof):
        with app.app_context():
            result = ProofService.archive_proof(proof.id)
            session.commit()
            assert result.statut == 'ARCHIVE'

    def test_archive_nonexistent(self, app, session):
        with app.app_context():
            result = ProofService.archive_proof(9999)
            assert result is None


class TestProofServiceHardDelete:
    def test_hard_delete(self, app, session, proof):
        with app.app_context():
            proof_id = proof.id
            result = ProofService.hard_delete_proof(proof_id)
            session.commit()
            assert result is not None
            assert db.session.get(ProofMaster, proof_id) is None

    def test_hard_delete_nonexistent(self, app, session):
        with app.app_context():
            result = ProofService.hard_delete_proof(9999)
            assert result is None


class TestProofServiceReplace:
    def test_replace_proof(self, app, session, entreprise, proof, manager_user):
        with app.app_context():
            new_proof = ProofMaster(
                entreprise_id=entreprise.id,
                domaine='hse',
                nom_fichier='new_doc.pdf',
                type='pdf',
                chemin='preuves/1/new_doc.pdf',
                hash_fichier='newhash',
                statut='ACTIF',
            )
            session.add(new_proof)
            session.flush()

            ProofService.attach_proof(
                entreprise.id, 'evaluation_article', 1, proof.id, manager_user.id
            )
            session.commit()

            result = ProofService.replace_proof(proof.id, new_proof.id)
            session.commit()

            assert result.id == new_proof.id
            old = db.session.get(ProofMaster, proof.id)
            assert old.statut == 'REMPLACE'
            assert new_proof.remplace_preuve_id == proof.id

            refs = ProofReference.query.filter_by(proof_master_id=new_proof.id).all()
            assert len(refs) == 1
            assert refs[0].entity_type == 'evaluation_article'
            assert refs[0].entity_id == 1

    def test_replace_nonexistent(self, app, session):
        with app.app_context():
            result = ProofService.replace_proof(9999, 9998)
            assert result is None
