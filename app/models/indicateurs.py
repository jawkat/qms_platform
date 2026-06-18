from app import db
from datetime import datetime


class Indicateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    description = db.Column(db.Text)
    formule = db.Column(db.Text)
    periode = db.Column(db.String(50))
    calcul_auto = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    valeurs = db.relationship('IndicateurValeur', back_populates='indicateur')


class IndicateurValeur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    indicateur_id = db.Column(db.Integer, db.ForeignKey('indicateur.id'))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    date_calcul = db.Column(db.Date)
    valeur = db.Column(db.Float)

    indicateur = db.relationship('Indicateur', back_populates='valeurs')
    entreprise = db.relationship('Entreprise')
