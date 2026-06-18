from app import db
from datetime import datetime
from enum import Enum

class Risque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    designation = db.Column(db.String(200), nullable=False)
    cause = db.Column(db.Text)
    effet = db.Column(db.Text)
    gravite = db.Column(db.Integer, default=1)
    probabilite = db.Column(db.Integer, default=1)
    detection = db.Column(db.Integer, default=1)
    maitrise = db.Column(db.Text)
    statut = db.Column(db.String(20), default='identifie')
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur')

    @property
    def ipr(self):
        return self.gravite * self.probabilite * self.detection

class ProcessusHaccp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    etape = db.Column(db.String(200), nullable=False)
    danger = db.Column(db.Text)
    maitrise = db.Column(db.Text)
    limite_critique = db.Column(db.String(200))
    surveillance = db.Column(db.Text)
    action_corrective = db.Column(db.Text)
    est_ccp = db.Column(db.Boolean, default=False)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

class ReclamationClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_reclamation = db.Column(db.Date, nullable=False)
    client = db.Column(db.String(100), nullable=False)
    produit = db.Column(db.String(200))
    description = db.Column(db.Text)
    action = db.Column(db.Text)
    statut = db.Column(db.String(20), default='ouverte')
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur')

class Fournisseur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    produit = db.Column(db.String(200))
    evaluation = db.Column(db.Integer)
    statut = db.Column(db.String(20), default='actif')
    dernier_audit = db.Column(db.Date)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

class Formation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    formateur = db.Column(db.String(100))
    participants = db.Column(db.Text)
    date_formation = db.Column(db.Date)
    duree_heures = db.Column(db.Float)
    statut = db.Column(db.String(20), default='planifiee')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

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

class NonConformiteQualite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_nc = db.Column(db.Date, nullable=False)
    reference = db.Column(db.String(50))
    produit_processus = db.Column(db.String(200))
    description = db.Column(db.Text)
    action_corrective = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='ouverte')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur')
