from app.extensions import db
from .base import BaseModel


class PlanAnalyse(BaseModel):
    __tablename__ = 'labo_plan_analyse'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    produit_concerne = db.Column(db.String(200))
    parametre = db.Column(db.String(100))
    methode = db.Column(db.String(100))
    frequence = db.Column(db.String(100))
    seuil_min = db.Column(db.Float)
    seuil_max = db.Column(db.Float)
    unite = db.Column(db.String(20))
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')


class Echantillon(BaseModel):
    __tablename__ = 'labo_echantillon'
    code_externe = db.Column(db.String(100))
    date_prelevement = db.Column(db.DateTime, nullable=False)
    preleve_par = db.Column(db.String(100))
    type_produit = db.Column(db.String(100))
    lot = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='reçu')  # reçu, en_analyse, terminé
    
    entreprise = db.relationship('Entreprise')


class ResultatAnalyse(BaseModel):
    __tablename__ = 'labo_resultat'
    echantillon_id = db.Column(db.Integer, db.ForeignKey('labo_echantillon.id'), nullable=False)
    parametre = db.Column(db.String(100), nullable=False)
    valeur = db.Column(db.String(100))
    unite = db.Column(db.String(20))
    conforme = db.Column(db.Boolean)
    commentaire = db.Column(db.Text)
    
    entreprise = db.relationship('Entreprise')
    echantillon = db.relationship('Echantillon', backref='resultats')
