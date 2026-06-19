"""Modèles pour le module Connaissances."""
from app import db
from datetime import datetime


class REX(db.Model):
    __tablename__ = 'rex'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))  # incident, amelioration, best_practice, lecon
    contexte = db.Column(db.Text)
    causes = db.Column(db.Text)
    actions_menees = db.Column(db.Text)
    resultats = db.Column(db.Text)
    lecons_apprises = db.Column(db.Text)
    auteur = db.Column(db.String(100))
    date_rex = db.Column(db.Date)
    statut = db.Column(db.String(20), default='brouillon')  # brouillon, publie
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class FAQ(db.Model):
    __tablename__ = 'faq'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    question = db.Column(db.String(500), nullable=False)
    reponse = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(50))
    vue_count = db.Column(db.Integer, default=0)
    utile_count = db.Column(db.Integer, default=0)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
