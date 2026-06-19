"""Modèles pour le module Planification."""
from app import db
from datetime import datetime


class EvenementPlanification(db.Model):
    __tablename__ = 'evenement_planification'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type_evenement = db.Column(db.String(50))  # audit, formation, inspection, maintenance, reunion, echeance
    module_source = db.Column(db.String(50))  # haccp, hse, qualite, etc.
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime)
    lieu = db.Column(db.String(200))
    responsable = db.Column(db.String(100))
    rappel_avant = db.Column(db.Integer, default=7)  # jours avant
    statut = db.Column(db.String(20), default='planifie')  # planifie, en_cours, termine, annule
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
