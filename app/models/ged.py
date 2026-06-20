from app.extensions import db
from .base import BaseModel, TimestampMixin


class Dossier(BaseModel):
    __tablename__ = 'dossier'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('dossier.id', ondelete='SET NULL'), nullable=True)
    domaine = db.Column(db.String(20), default='hse', nullable=False)

    parent = db.relationship('Dossier', remote_side='Dossier.id', backref='sous_dossiers')
    entreprise = db.relationship('Entreprise')


class TypeDocument(BaseModel):
    __tablename__ = 'type_document'
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    schema_metadonnees = db.Column(db.JSON, default=dict)
    domaine = db.Column(db.String(20), default='hse', nullable=False)

    entreprise = db.relationship('Entreprise')


class WorkflowLog(db.Model, TimestampMixin):
    __tablename__ = 'workflow_log'
    proof_master_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    commentaire = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    metadata_avant = db.Column(db.JSON, default=dict)
    metadata_apres = db.Column(db.JSON, default=dict)

    proof = db.relationship('ProofMaster')
    utilisateur = db.relationship('Utilisateur')


class HistoriqueDocument(db.Model, TimestampMixin):
    __tablename__ = 'historique_document'
    document_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    champ_modifie = db.Column(db.String(100))
    valeur_avant = db.Column(db.Text)
    valeur_apres = db.Column(db.Text)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    document = db.relationship('ProofMaster', backref='historique')
    auteur = db.relationship('Utilisateur')
