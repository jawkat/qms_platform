"""Service layer pour le module GED / Documents."""

from datetime import date, datetime
from flask import current_app
from app import db
from app.models import ProofMaster, ProofReference, Dossier, TypeDocument, WorkflowLog, Utilisateur


class DocumentService:
    """Logique metier pour les documents GED."""

    @staticmethod
    def compute_stats(entreprise_id, proofs):
        """Calcule les statistiques de workflow pour une liste de preuves."""
        return {
            'total': len(proofs),
            'brouillon': sum(1 for p in proofs if p.workflow_statut == 'brouillon'),
            'soumis': sum(1 for p in proofs if p.workflow_statut == 'soumis'),
            'approuve': sum(1 for p in proofs if p.workflow_statut == 'approuve'),
            'expire': sum(1 for p in proofs if p.validite and p.validite < date.today()),
            'expire_bientot': sum(
                1 for p in proofs
                if p.validite and p.validite >= date.today()
                and (p.validite - date.today()).days <= 30
            ),
        }

    @staticmethod
    def compute_pending_approvals(proofs, user_id):
        """Compte les documents en attente d'approbation pour un utilisateur."""
        return sum(
            1 for p in proofs
            if p.workflow_statut == 'soumis' and p.workflow_approbateur_id == user_id
        )

    @staticmethod
    def build_version_chain(proof):
        """Construit la chaine de versions d'un document."""
        versions = []
        v = proof
        while v:
            versions.append(v)
            if v.remplace_preuve_id:
                v = ProofMaster.query.get(v.remplace_preuve_id)
            else:
                v = None
        return versions

    @staticmethod
    def log_workflow(proof_id, action, commentaire, user_id):
        """Enregistre un evenement dans le journal de workflow."""
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

    @staticmethod
    def build_dossier_tree(entreprise_id, domaine=None):
        """Construit l'arborescence des dossiers."""
        query = Dossier.query.filter_by(entreprise_id=entreprise_id)
        if domaine:
            query = query.filter_by(domaine=domaine)
        dossiers = query.order_by(Dossier.nom).all()

        doc_counts = {
            d.id: ProofMaster.query.filter_by(
                dossier_id=d.id, statut='ACTIF'
            ).count() for d in dossiers
        }

        def build_tree(parent_id=None):
            from app.schemas.documents import DossierSchema
            items = [d for d in dossiers if d.parent_id == parent_id]
            result = []
            for d in items:
                data = DossierSchema().dump(d)
                data['doc_count'] = doc_counts.get(d.id, 0)
                data['children'] = build_tree(d.id)
                result.append(data)
            return result

        return build_tree(None)

    @staticmethod
    def generate_numero_document():
        """Genere un numero de document unique."""
        last_num = db.session.query(func.max(ProofMaster.id)).scalar() or 0
        return f"DOC-{datetime.utcnow().strftime('%Y%m')}-{last_num + 1:04d}"

    @staticmethod
    def apply_upload_metadata(proof, form_data, user_id, numero_doc=None):
        """Applique les metadonnees d'upload sur une preuve."""
        proof.dossier_id = form_data.get('dossier_id', type=int) or None
        proof.type_document_id = form_data.get('type_document_id', type=int) or None
        if numero_doc:
            proof.numero_document = numero_doc
        proof.mots_cles = form_data.get('mots_cles')
        proof.notes = form_data.get('notes')
        proof.workflow_statut = form_data.get('workflow_statut', 'brouillon')
        proof.workflow_approbateur_id = form_data.get('workflow_approbateur_id', type=int) or None
        if proof.workflow_statut == 'soumis' and proof.workflow_approbateur_id:
            proof.date_soumission = datetime.utcnow()
            DocumentService.log_workflow(proof.id, 'soumis', 'Soumis pour approbation', user_id)

    @staticmethod
    def create_new_version(old_proof, new_file_proof, form_data, user_id):
        """Cree une nouvelle version et archive l'ancienne."""
        old_version = int(old_proof.version) if old_proof.version and old_proof.version.isdigit() else 1
        new_version = str(old_version + 1)

        new_file_proof.dossier_id = old_proof.dossier_id
        new_file_proof.type_document_id = old_proof.type_document_id
        new_file_proof.numero_document = old_proof.numero_document
        new_file_proof.mots_cles = old_proof.mots_cles
        new_file_proof.notes = form_data.get('notes') or old_proof.notes
        new_file_proof.workflow_statut = 'brouillon'
        new_file_proof.version = new_version

        DocumentService.log_workflow(
            old_proof.id, 'nouvelle_version',
            f'Nouvelle version {new_version} uploadée',
            user_id
        )

        old_proof.statut = 'REMPLACE'
        new_file_proof.remplace_preuve_id = old_proof.id
        return new_file_proof, new_version


from sqlalchemy import func
