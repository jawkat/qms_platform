"""Modèles pour le module Environnement (ISO 14001)."""
from app import db
from datetime import datetime


class AspectEnvironnemental(db.Model):
    __tablename__ = 'aspect_environnemental'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))  # dechets, emission, bruit, eau, energie
    impact = db.Column(db.Text)
    gravite = db.Column(db.String(20), default='moyenne')  # faible, moyenne, forte, critique
    maitrise = db.Column(db.Text)
    responsable = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class SuiviEnvironnemental(db.Model):
    __tablename__ = 'suivi_environnemental'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    aspect_id = db.Column(db.Integer, db.ForeignKey('aspect_environnemental.id'))
    type_suivi = db.Column(db.String(50))  # dechets, emission_co2, eau, energie
    valeur = db.Column(db.Float)
    unite = db.Column(db.String(20))  # kg, m3, kWh, tonnes
    periode = db.Column(db.String(20))  # mensuel, trimestriel, annuel
    date_mesure = db.Column(db.Date)
    commentaire = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    aspect = db.relationship('AspectEnvironnemental')
