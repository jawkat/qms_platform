"""Modèles pour le module Réunions."""
from app import db
from datetime import datetime


class Reunion(db.Model):
    __tablename__ = 'reunion'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    titre = db.Column(db.String(200), nullable=False)
    type_reunion = db.Column(db.String(50))  # qualite, haccp, securite, revue_direction
    description = db.Column(db.Text)
    date_reunion = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200))
    organisateur = db.Column(db.String(100))
    participants = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifiee')  # planifiee, en_cours, terminee
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class CompteRendu(db.Model):
    __tablename__ = 'compte_rendu'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    reunion_id = db.Column(db.Integer, db.ForeignKey('reunion.id'), nullable=False)
    ordre_du_jour = db.Column(db.Text)
    decisions = db.Column(db.Text)
    resume = db.Column(db.Text)
    redige_par = db.Column(db.String(100))
    date_redaction = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    reunion = db.relationship('Reunion')


class ActionReunion(db.Model):
    __tablename__ = 'action_reunion'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    reunion_id = db.Column(db.Integer, db.ForeignKey('reunion.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsable = db.Column(db.String(100))
    echeance = db.Column(db.Date)
    statut = db.Column(db.String(20), default='a_faire')  # a_faire, en_cours, terminee
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    reunion = db.relationship('Reunion')
