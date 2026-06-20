from app.extensions import db
from .base import BaseModel, TimestampMixin


class Indicateur(db.Model, TimestampMixin):
    __tablename__ = 'indicateur'
    nom = db.Column(db.String(100))
    description = db.Column(db.Text)
    formule = db.Column(db.Text)
    periode = db.Column(db.String(50))
    calcul_auto = db.Column(db.Boolean, default=True)
    valeurs = db.relationship('IndicateurValeur', back_populates='indicateur')


class IndicateurValeur(BaseModel):
    __tablename__ = 'indicateur_valeur'
    indicateur_id = db.Column(db.Integer, db.ForeignKey('indicateur.id'))
    date_calcul = db.Column(db.Date)
    valeur = db.Column(db.Float)

    indicateur = db.relationship('Indicateur', back_populates='valeurs')
    entreprise = db.relationship('Entreprise')
