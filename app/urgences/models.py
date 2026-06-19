"""Modèles pour le module Urgences."""
from app import db
from datetime import datetime


class PlanUrgence(db.Model):
    __tablename__ = 'plan_urgence'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    nom = db.Column(db.String(200), nullable=False)
    type_urgence = db.Column(db.String(50))  # incendie, accident, pollution, autre
    description = db.Column(db.Text)
    procedures = db.Column(db.Text)
    contacts_cles = db.Column(db.JSON, default=list)  # [{nom, telephone, role}]
    materiel = db.Column(db.Text)
    date_derniere_revu = db.Column(db.Date)
    date_prochaine_revu = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class ExerciceEvacuation(db.Model):
    __tablename__ = 'exercice_evacuation'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    plan_urgence_id = db.Column(db.Integer, db.ForeignKey('plan_urgence.id'))
    date_exercice = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200))
    responsable = db.Column(db.String(100))
    participants = db.Column(db.Integer)
    duree_minutes = db.Column(db.Integer)
    resultat = db.Column(db.Text)
    observations = db.Column(db.Text)
    ameliorations = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifie')  # planifie, realise
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    plan = db.relationship('PlanUrgence')


class MainCourante(db.Model):
    __tablename__ = 'main_courante'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    date_evenement = db.Column(db.DateTime, nullable=False)
    type_evenement = db.Column(db.String(50))  # incident, urgence, exercice, info
    description = db.Column(db.Text, nullable=False)
    lieu = db.Column(db.String(200))
    declares_par = db.Column(db.String(100))
    actions_entreprises = db.Column(db.Text)
    statut = db.Column(db.String(20), default='ouvert')  # ouvert, en_cours, cloture
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
