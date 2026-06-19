from app import db
from datetime import datetime, date


class Incident(db.Model):
    __tablename__ = 'incident'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
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
    statut = db.Column(db.String(20), default='ouvert')
    gravite = db.Column(db.String(20), default='majeur')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_cloture = db.Column(db.Date)
    action_corrective_id = db.Column(db.Integer, db.ForeignKey('action_corrective.id'))
    entreprise = db.relationship('Entreprise')
    declarant = db.relationship('Utilisateur', foreign_keys=[declarant_id])
    action_corrective = db.relationship('ActionCorrective')


class EPI(db.Model):
    __tablename__ = 'epi'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
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
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    utilisateur_affecte = db.relationship('Utilisateur', foreign_keys=[utilisateur_affecte_id])


class Inspection(db.Model):
    __tablename__ = 'inspection'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    type_inspection = db.Column(db.String(30), nullable=False)
    date_inspection = db.Column(db.Date, nullable=False, default=date.today)
    lieu = db.Column(db.String(200))
    zone = db.Column(db.String(100))
    inspecteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    observations = db.Column(db.Text)
    anomalies_detectees = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(20), default='en_cours')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    inspecteur = db.relationship('Utilisateur', foreign_keys=[inspecteur_id])
    items = db.relationship('InspectionItem', backref='inspection', lazy='dynamic',
                            cascade='all, delete-orphan')


class InspectionItem(db.Model):
    __tablename__ = 'inspection_item'
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspection.id'), nullable=False)
    checklist_item = db.Column(db.Text, nullable=False)
    conforme = db.Column(db.Boolean)
    observation = db.Column(db.Text)


class PermisTravail(db.Model):
    __tablename__ = 'permis_travail'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
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
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    demandant = db.relationship('Utilisateur', foreign_keys=[demandant_id])
    responsable_securite = db.relationship('Utilisateur', foreign_keys=[responsable_securite_id])
    authorizeur = db.relationship('Utilisateur', foreign_keys=[authorizeur_id])
