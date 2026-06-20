from app.extensions import db
from datetime import datetime, date
from enum import Enum
from .base import BaseModel, TimestampMixin


class TypeMethodeAnalyse(str, Enum):
    ARBRE_CAUSES = 'arbre_des_causes'
    CINQ_POURQUOI = 'cinq_pourquoi'
    ISHIKAWA = 'ishikawa'
    AMDEC = 'amdec'


class Incident(BaseModel):
    __tablename__ = 'incident'
    type_incident = db.Column(db.String(30), nullable=False)
    date_incident = db.Column(db.Date, nullable=False, default=date.today)
    lieu = db.Column(db.String(200))
    zone = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    victimes = db.Column(db.Text)
    type_blessure = db.Column(db.Text)
    jours_arret = db.Column(db.Integer, default=0)
    temoins = db.Column(db.Text)
    declarant_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    cause_initiale = db.Column(db.Text)
    analyse_racine = db.Column(db.Text)
    methode_analyse = db.Column(db.String(20), default='arbre_des_causes')
    statut = db.Column(db.String(20), default='ouvert')
    gravite = db.Column(db.String(20), default='majeur')
    date_cloture = db.Column(db.Date)
    action_corrective_id = db.Column(db.Integer, db.ForeignKey('action_corrective.id'))
    
    entreprise = db.relationship('Entreprise')
    declarant = db.relationship('Utilisateur', foreign_keys=[declarant_id])
    action_corrective = db.relationship('ActionCorrective')
    causes = db.relationship('CauseIncident', backref='incident', lazy='dynamic',
                              cascade='all, delete-orphan', order_by='CauseIncident.ordre')


class UniteTravail(BaseModel):
    __tablename__ = 'unite_travail'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    service = db.Column(db.String(100))
    effectif = db.Column(db.Integer, default=0)
    horaires = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')
    dangers = db.relationship('DangerSst', backref='unite_travail', lazy='dynamic',
                               cascade='all, delete-orphan')


class DangerSst(BaseModel):
    __tablename__ = 'danger_sst'
    unite_travail_id = db.Column(db.Integer, db.ForeignKey('unite_travail.id'), nullable=False)
    famille_danger = db.Column(db.String(30), nullable=False)  # physique, chimique, biologique, ergonomique, psychosocial, accident
    danger = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    source = db.Column(db.String(200))
    consequence = db.Column(db.Text)
    mesures_existantes = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')
    evaluations = db.relationship('EvaluationRisqueSst', backref='danger_sst', lazy='dynamic',
                                   cascade='all, delete-orphan')


class EvaluationRisqueSst(BaseModel):
    __tablename__ = 'evaluation_risque_sst'
    danger_id = db.Column(db.Integer, db.ForeignKey('danger_sst.id'), nullable=False)
    gravite = db.Column(db.Integer, default=1)        # 1-4
    probabilite = db.Column(db.Integer, default=1)     # 1-4
    frequence = db.Column(db.Integer, default=1)        # 1-4
    maitrise = db.Column(db.Integer, default=1)         # 1-4 (inverse: 1=pas maîtrisé, 4=totalement)
    plan_action = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_echeance = db.Column(db.Date)
    date_revu = db.Column(db.Date)
    statut = db.Column(db.String(20), default='a_traiter')
    
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur', foreign_keys=[responsable_id])

    @property
    def criticite(self):
        return self.gravite * self.probabilite * self.frequence

    @property
    def niveau_risque(self):
        c = self.criticite
        if c >= 27: return 'critique'
        if c >= 18: return 'eleve'
        if c >= 9: return 'moyen'
        return 'faible'

    @property
    def maitrise_score(self):
        return 4 - self.maitrise  # inversion pour l'affichage


class CauseIncident(BaseModel):
    __tablename__ = 'cause_incident'
    incident_id = db.Column(db.Integer, db.ForeignKey('incident.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('cause_incident.id'), nullable=True)
    categorie = db.Column(db.String(30), default='autre')  # main_oeuvre, methode, milieu, matiere, machine, autre
    description = db.Column(db.Text, nullable=False)
    ordre = db.Column(db.Integer, default=0)
    
    entreprise = db.relationship('Entreprise')
    parent = db.relationship('CauseIncident', remote_side='CauseIncident.id', backref='enfants')


class EPI(BaseModel):
    __tablename__ = 'epi'
    type_epi = db.Column(db.String(50), nullable=False)
    designation = db.Column(db.String(200), nullable=False)
    marque = db.Column(db.String(100))
    modele = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    norme_reference = db.Column(db.String(100))
    date_fabrication = db.Column(db.Date)
    date_peremption = db.Column(db.Date)
    duree_vie_mois = db.Column(db.Integer)
    statut = db.Column(db.String(20), default='en_service')
    utilisateur_affecte_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    stock_emplacement = db.Column(db.String(100))
    prochain_controle = db.Column(db.Date)
    certificat_conformite = db.Column(db.Boolean, default=False)
    
    entreprise = db.relationship('Entreprise')
    utilisateur_affecte = db.relationship('Utilisateur', foreign_keys=[utilisateur_affecte_id])


class Inspection(BaseModel):
    __tablename__ = 'inspection'
    type_inspection = db.Column(db.String(30), nullable=False)
    date_inspection = db.Column(db.Date, nullable=False, default=date.today)
    lieu = db.Column(db.String(200))
    zone = db.Column(db.String(100))
    inspecteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    observations = db.Column(db.Text)
    anomalies_detectees = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(20), default='en_cours')
    
    entreprise = db.relationship('Entreprise')
    inspecteur = db.relationship('Utilisateur', foreign_keys=[inspecteur_id])
    items = db.relationship('InspectionItem', backref='inspection', lazy='dynamic',
                             cascade='all, delete-orphan')


class InspectionItem(db.Model, TimestampMixin): # Use TimestampMixin because it doesn't need entreprise_id (inherited via Inspection)
    __tablename__ = 'inspection_item'
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    checklist_item = db.Column(db.Text, nullable=False)
    conforme = db.Column(db.Boolean)
    observation = db.Column(db.Text)


class PermisTravail(BaseModel):
    __tablename__ = 'permis_travail'
    type_permis = db.Column(db.String(30), nullable=False)
    date_permis = db.Column(db.Date, nullable=False, default=date.today)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    lieu = db.Column(db.String(200))
    intervention_description = db.Column(db.Text)
    demandant_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    responsable_securite_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    authorizeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    risques_identifies = db.Column(db.Text)
    mesures_preventives = db.Column(db.Text)
    consignes_securite = db.Column(db.Text)
    statut = db.Column(db.String(20), default='en_attente')
    
    entreprise = db.relationship('Entreprise')
    demandant = db.relationship('Utilisateur', foreign_keys=[demandant_id])
    responsable_securite = db.relationship('Utilisateur', foreign_keys=[responsable_securite_id])
    authorizeur = db.relationship('Utilisateur', foreign_keys=[authorizeur_id])
