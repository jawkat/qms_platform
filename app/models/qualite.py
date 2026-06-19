from app import db
from datetime import datetime
from enum import Enum

class Risque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='qualite')
    designation = db.Column(db.String(200), nullable=False)
    cause = db.Column(db.Text)
    effet = db.Column(db.Text)
    gravite = db.Column(db.Integer, default=1)
    probabilite = db.Column(db.Integer, default=1)
    detection = db.Column(db.Integer, default=1)
    maitrise = db.Column(db.Text)
    statut = db.Column(db.String(20), default='identifie')
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    categorie = db.Column(db.String(50))
    processus_concerne = db.Column(db.String(200))
    plan_traitement = db.Column(db.Text)
    action_preventive = db.Column(db.Text)
    action_corrective = db.Column(db.Text)
    date_revu = db.Column(db.Date)
    date_prochaine_revu = db.Column(db.Date)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur')

    @property
    def ipr(self):
        return self.gravite * self.probabilite * self.detection

    @property
    def niveau_risque(self):
        ipr = self.ipr
        if ipr >= 80: return 'critique'
        if ipr >= 40: return 'eleve'
        if ipr >= 15: return 'moyen'
        return 'faible'

class Equipement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    modele = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    derniere_maintenance = db.Column(db.Date)
    prochaine_maintenance = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

class ControleQualite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_controle = db.Column(db.Date, nullable=False)
    produit = db.Column(db.String(200))
    lot = db.Column(db.String(100))
    type_controle = db.Column(db.String(100))
    resultat = db.Column(db.String(20))
    valeur = db.Column(db.String(100))
    specification = db.Column(db.String(100))
    inspecteur = db.Column(db.String(100))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

class RevueDirection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_revue = db.Column(db.Date, nullable=False)
    participants = db.Column(db.Text)
    decisions = db.Column(db.Text)
    suivi = db.Column(db.Text)
    statut = db.Column(db.String(20), default='realisee')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
