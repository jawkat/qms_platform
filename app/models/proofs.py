from app import db
from datetime import datetime


class ProofMaster(db.Model):
    __tablename__ = 'proof_master'

    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='hse', nullable=False, index=True)

    nom_fichier = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50))
    chemin = db.Column(db.String(255), nullable=False)
    taille_bytes = db.Column(db.Integer)
    hash_fichier = db.Column(db.String(64))
    description = db.Column(db.Text)
    validite = db.Column(db.Date)
    categorie = db.Column(db.String(50))
    version = db.Column(db.String(20), default='1')
    statut = db.Column(db.String(50), default='ACTIF')

    upload_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remplace_preuve_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'))
    extra_metadata = db.Column(db.JSON, default=dict)
    reference_count = db.Column(db.Integer, default=0)

    entreprise = db.relationship('Entreprise')
    uploader = db.relationship('Utilisateur', foreign_keys=[upload_par])

    references = db.relationship(
        'ProofReference', back_populates='proof_master',
        cascade='all, delete-orphan', foreign_keys='ProofReference.proof_master_id'
    )

    __table_args__ = (
        db.Index('idx_proof_entreprise_statut', 'entreprise_id', 'statut'),
        db.Index('idx_proof_hash', 'hash_fichier'),
        db.UniqueConstraint('entreprise_id', 'hash_fichier', name='uq_entreprise_hash'),
    )


class ProofReference(db.Model):
    __tablename__ = 'proof_reference'

    id = db.Column(db.Integer, primary_key=True)
    proof_master_id = db.Column(db.Integer, db.ForeignKey('proof_master.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    date_attached = db.Column(db.DateTime, default=datetime.utcnow)
    attached_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    validite_override = db.Column(db.Date)
    description_override = db.Column(db.Text)
    extra_metadata = db.Column(db.JSON, default=dict)

    proof_master = db.relationship('ProofMaster', back_populates='references')
    attached_by_user = db.relationship('Utilisateur')

    __table_args__ = (
        db.UniqueConstraint('proof_master_id', 'entity_type', 'entity_id', name='uq_proof_entity'),
        db.Index('idx_ref_entity', 'entity_type', 'entity_id'),
    )
