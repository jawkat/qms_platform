"""Modèles pour le module Maintenance."""
from app import db
from datetime import datetime


class EquipementMaintenance(db.Model):
    __tablename__ = 'equipement_maintenance'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    nom = db.Column(db.String(200), nullable=False)
    reference = db.Column(db.String(100))
    description = db.Column(db.Text)
    localisation = db.Column(db.String(200))
    categorie = db.Column(db.String(50))  #machine, outil, vehicule, batiment
    date_acquisition = db.Column(db.Date)
    date_derniere_maintenance = db.Column(db.Date)
    date_prochaine_maintenance = db.Column(db.Date)
    frequence_maintenance = db.Column(db.String(50))  # hebdo, mensuel, trimestriel, annuel
    statut = db.Column(db.String(20), default='actif')  # actif, en_panne, maintenance
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class InterventionMaintenance(db.Model):
    __tablename__ = 'intervention_maintenance'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    equipement_id = db.Column(db.Integer, db.ForeignKey('equipement_maintenance.id'), nullable=False)
    type_intervention = db.Column(db.String(50))  # preventive, corrective, amelioration
    description = db.Column(db.Text, nullable=False)
    responsable = db.Column(db.String(100))
    date_debut = db.Column(db.DateTime)
    date_fin = db.Column(db.DateTime)
    cout = db.Column(db.Numeric(10, 2))
    pieces_rechange = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifiee')  # planifiee, en_cours, terminee
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    equipement = db.relationship('EquipementMaintenance')
