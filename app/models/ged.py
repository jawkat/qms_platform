from app import db
from datetime import datetime


class Dossier(db.Model):
    __tablename__ = 'dossier'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('dossier.id', ondelete='SET NULL'), nullable=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='hse', nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship('Dossier', remote_side='Dossier.id', backref='sous_dossiers')
    entreprise = db.relationship('Entreprise')


class TypeDocument(db.Model):
    __tablename__ = 'type_document'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    schema_metadonnees = db.Column(db.JSON, default=dict)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='hse', nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')


class WorkflowLog(db.Model):
    __tablename__ = 'workflow_log'

    id = db.Column(db.Integer, primary_key=True)
    proof_master_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    commentaire = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    metadata_avant = db.Column(db.JSON, default=dict)
    metadata_apres = db.Column(db.JSON, default=dict)

    proof = db.relationship('ProofMaster')
    utilisateur = db.relationship('Utilisateur')


class HistoriqueDocument(db.Model):
    __tablename__ = 'historique_document'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False)
    action = db.Column(db.String(30), nullable=False)
    champ_modifie = db.Column(db.String(100))
    valeur_avant = db.Column(db.Text)
    valeur_apres = db.Column(db.Text)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    document = db.relationship('ProofMaster', backref='historique')
    auteur = db.relationship('Utilisateur')
