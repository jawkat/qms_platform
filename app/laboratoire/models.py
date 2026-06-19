"""Modèles pour le module Laboratoire."""
from app import db
from datetime import datetime


class PlanAnalyse(db.Model):
    __tablename__ = 'plan_analyse'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    produit_concerne = db.Column(db.String(200))
    parametre = db.Column(db.String(200))
    methode = db.Column(db.String(200))
    frequence = db.Column(db.String(100))
    seuil_min = db.Column(db.Float)
    seuil_max = db.Column(db.Float)
    unite = db.Column(db.String(20))
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class Echantillon(db.Model):
    __tablename__ = 'echantillon'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    plan_analyse_id = db.Column(db.Integer, db.ForeignKey('plan_analyse.id'))
    code = db.Column(db.String(50), nullable=False)
    produit = db.Column(db.String(200))
    lot = db.Column(db.String(100))
    date_prelevement = db.Column(db.DateTime)
    preleve_par = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='en_attente')  # en_attente, analyse, valide
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    plan = db.relationship('PlanAnalyse')


class ResultatAnalyse(db.Model):
    __tablename__ = 'resultat_analyse'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    echantillon_id = db.Column(db.Integer, db.ForeignKey('echantillon.id'), nullable=False)
    parametre = db.Column(db.String(200))
    valeur = db.Column(db.Float)
    unite = db.Column(db.String(20))
    conforme = db.Column(db.Boolean, default=True)
    commentaire = db.Column(db.Text)
    analyse_par = db.Column(db.String(100))
    date_analyse = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    echantillon = db.relationship('Echantillon')
