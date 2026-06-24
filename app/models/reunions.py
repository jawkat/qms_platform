from app.extensions import db
from .base import BaseModel


class Reunion(BaseModel):
    __tablename__ = 'reunion'
    titre = db.Column(db.String(200), nullable=False)
    date_reunion = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(100))
    type_reunion = db.Column(db.String(50))
    organisateur = db.Column(db.String(100))
    ordre_du_jour = db.Column(db.Text)
    participants = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifiee')  # planifiee, en_cours, terminee, annulee
    
    entreprise = db.relationship('Entreprise')
    compte_rendu = db.relationship('CompteRendu', back_populates='reunion', uselist=False, cascade='all, delete-orphan')


class CompteRendu(BaseModel):
    __tablename__ = 'compte_rendu'
    reunion_id = db.Column(db.Integer, db.ForeignKey('reunion.id'), nullable=False, unique=True)
    contenu = db.Column(db.Text)
    redacteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_publication = db.Column(db.DateTime)
    
    reunion = db.relationship('Reunion', back_populates='compte_rendu')
    redacteur = db.relationship('Utilisateur')
    actions = db.relationship('ActionReunion', back_populates='compte_rendu', cascade='all, delete-orphan')


class ActionReunion(BaseModel):
    __tablename__ = 'action_reunion'
    compte_rendu_id = db.Column(db.Integer, db.ForeignKey('compte_rendu.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_echeance = db.Column(db.Date)
    statut = db.Column(db.String(20), default='a_faire')
    
    compte_rendu = db.relationship('CompteRendu', back_populates='actions')
    responsable = db.relationship('Utilisateur')
