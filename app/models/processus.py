from app.extensions import db
from .base import BaseModel


class Processus(BaseModel):
    __tablename__ = 'processus'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_processus = db.Column(db.String(50), default='operationnel')
    proprietaire_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    processus_parent_id = db.Column(db.Integer, db.ForeignKey('processus.id'), nullable=True)
    entree = db.Column(db.Text)
    sortie = db.Column(db.Text)
    objectifs = db.Column(db.Text)
    risques_associes = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    date_derniere_revu = db.Column(db.Date)
    date_prochaine_revu = db.Column(db.Date)
    extra_metadata = db.Column(db.JSON, default=dict)

    entreprise = db.relationship('Entreprise')
    proprietaire = db.relationship('Utilisateur', foreign_keys=[proprietaire_id])
    sous_processus = db.relationship('Processus', backref=db.backref('parent', remote_side='Processus.id'))


class IndicateurProcessus(db.Model):
    __tablename__ = 'indicateur_processus'
    id = db.Column(db.Integer, primary_key=True)
    processus_id = db.Column(db.Integer, db.ForeignKey('processus.id'), nullable=False)
    indicateur_id = db.Column(db.Integer, db.ForeignKey('indicateur.id'), nullable=False)
    objectif = db.Column(db.Float)
    
    processus = db.relationship('Processus', backref='indicateurs')
    indicateur = db.relationship('Indicateur')
