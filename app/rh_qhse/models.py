"""Modèles pour le module RH QHSE."""
from app import db
from datetime import datetime


class EmployeQHSE(db.Model):
    __tablename__ = 'employe_qhse'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    matricule = db.Column(db.String(50))
    poste = db.Column(db.String(100))
    department = db.Column(db.String(100))
    date_embauche = db.Column(db.Date)
    date_visite_medicale = db.Column(db.Date)
    date_prochaine_visite = db.Column(db.Date)
    habilitations = db.Column(db.JSON, default=list)  # liste des habilitations
    epi_attribues = db.Column(db.JSON, default=list)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    utilisateur = db.relationship('Utilisateur')
