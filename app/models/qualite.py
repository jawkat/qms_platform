from app import db
from datetime import datetime, date
from enum import Enum

class ObjectifQualite(db.Model):
    __tablename__ = 'objectif_qualite'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    indicateur_id = db.Column(db.Integer, db.ForeignKey('indicateur.id'), nullable=True)
    cible = db.Column(db.Float)
    seuil_alerte = db.Column(db.Float)
    pilote_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    date_debut = db.Column(db.Date)
    date_echeance = db.Column(db.Date)
    statut = db.Column(db.String(20), default='en_cours')  # en_cours, atteint, en_retard, non_atteint
    domaine = db.Column(db.String(20), default='qualite')
    processus_concerne = db.Column(db.String(200))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    pilote = db.relationship('Utilisateur', foreign_keys=[pilote_id])
    indicateur = db.relationship('Indicateur', foreign_keys=[indicateur_id])

    @property
    def progression(self):
        if not self.cible or self.cible == 0:
            return 0
        from app.models.indicateurs import IndicateurValeur
        derniere = IndicateurValeur.query.filter_by(
            indicateur_id=self.indicateur_id,
            entreprise_id=self.entreprise_id,
        ).order_by(IndicateurValeur.date_calcul.desc()).first()
        if not derniere:
            return 0
        return min(100, int((derniere.valeur / self.cible) * 100))


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
    __tablename__ = 'equipement'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    modele = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100))
    type_equipement = db.Column(db.String(30), default='production')  # production, mesure, essai, monitoring
    # Maintenance
    derniere_maintenance = db.Column(db.Date)
    prochaine_maintenance = db.Column(db.Date)
    # Métrologie
    frequence_etalonnage_jours = db.Column(db.Integer)
    precision = db.Column(db.String(50))
    unite_mesure = db.Column(db.String(20))
    tolerance_min = db.Column(db.Float)
    tolerance_max = db.Column(db.Float)
    date_dernier_etalonnage = db.Column(db.Date)
    date_prochain_etalonnage = db.Column(db.Date)
    organisme_etalonnage = db.Column(db.String(200))
    certificat_etalonnage = db.Column(db.String(200))
    statut_metrologique = db.Column(db.String(20), default='en_cours')  # en_cours, etalonne, expire, hors_service
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    etalonnages = db.relationship('EnregistrementEtalonnage', backref='equipement', lazy='dynamic',
                                   cascade='all, delete-orphan')


class EnregistrementEtalonnage(db.Model):
    __tablename__ = 'enregistrement_etalonnage'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    equipement_id = db.Column(db.Integer, db.ForeignKey('equipement.id'), nullable=False)
    date_etalonnage = db.Column(db.Date, nullable=False)
    valeur_mesuree = db.Column(db.Float)
    valeur_reference = db.Column(db.Float)
    ecart = db.Column(db.Float)
    conforme = db.Column(db.Boolean, default=True)
    certificat_id = db.Column(db.String(100))
    operateur = db.Column(db.String(100))
    notes = db.Column(db.Text)
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
