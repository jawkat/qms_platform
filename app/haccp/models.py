from app import db
from datetime import datetime, date
from enum import Enum


class TypeDanger(str, Enum):
    BIOLOGIQUE = 'biologique'
    CHIMIQUE = 'chimique'
    PHYSIQUE = 'physique'
    ALLERGENE = 'allergene'


class StatutHaccp(str, Enum):
    ACTIF = 'actif'
    INACTIF = 'inactif'


class ProcessusHaccp(db.Model):
    __tablename__ = 'haccp_processus'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    etape = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    danger = db.Column(db.Text)
    type_danger = db.Column(db.String(20), default='biologique')
    maitrise = db.Column(db.Text)
    limite_critique = db.Column(db.String(200))
    surveillance = db.Column(db.Text)
    frequence_surveillance = db.Column(db.String(100))
    action_corrective = db.Column(db.Text)
    est_ccp = db.Column(db.Boolean, default=False)
    num_ccp = db.Column(db.String(10))
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    analyses = db.relationship('AnalyseDanger', backref='processus', lazy='dynamic',
                               cascade='all, delete-orphan')


class ProduitHaccp(db.Model):
    __tablename__ = 'haccp_produit'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    reference = db.Column(db.String(50))
    description = db.Column(db.Text)
    duree_conservation = db.Column(db.String(100))
    conditions_stockage = db.Column(db.Text)
    utilisation_prevue = db.Column(db.Text)
    type_client = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    matieres_premieres = db.relationship('MatierePremiere', backref='produit', lazy='dynamic',
                                         cascade='all, delete-orphan')
    etapes = db.relationship('ProcessusHaccp', secondary='haccp_produit_processus',
                             backref=db.backref('produits', lazy='dynamic'))


produit_processus = db.Table('haccp_produit_processus',
    db.Column('produit_id', db.Integer, db.ForeignKey('haccp_produit.id')),
    db.Column('processus_id', db.Integer, db.ForeignKey('haccp_processus.id')),
)


class MatierePremiere(db.Model):
    __tablename__ = 'haccp_matiere_premiere'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('haccp_produit.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    fournisseur = db.Column(db.String(200))
    origine = db.Column(db.String(100))
    allergene = db.Column(db.Boolean, default=False)
    risque = db.Column(db.Text)
    specification = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class AnalyseDanger(db.Model):
    __tablename__ = 'haccp_analyse_danger'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    processus_id = db.Column(db.Integer, db.ForeignKey('haccp_processus.id'), nullable=False)
    type_danger = db.Column(db.String(20), nullable=False)
    danger = db.Column(db.Text, nullable=False)
    cause = db.Column(db.Text)
    gravite = db.Column(db.Integer, default=1)
    probabilite = db.Column(db.Integer, default=1)
    detectabilite = db.Column(db.Integer, default=1)
    mesure_preventive = db.Column(db.Text)
    est_significatif = db.Column(db.Boolean, default=False)
    justification = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

    @property
    def ipr(self):
        return self.gravite * self.probabilite * self.detectabilite


class Ccp(db.Model):
    __tablename__ = 'haccp_ccp'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    processus_id = db.Column(db.Integer, db.ForeignKey('haccp_processus.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    danger = db.Column(db.Text, nullable=False)
    limite_critique = db.Column(db.String(200), nullable=False)
    tolerance = db.Column(db.String(100))
    methode_surveillance = db.Column(db.Text)
    frequence_surveillance = db.Column(db.String(100))
    responsable = db.Column(db.String(100))
    action_corrective = db.Column(db.Text)
    procedure_derogation = db.Column(db.Text)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    processus = db.relationship('ProcessusHaccp')
    enregistrements = db.relationship('EnregistrementCcp', backref='ccp', lazy='dynamic',
                                      cascade='all, delete-orphan')


class EnregistrementCcp(db.Model):
    __tablename__ = 'haccp_enregistrement_ccp'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    ccp_id = db.Column(db.Integer, db.ForeignKey('haccp_ccp.id'), nullable=False)
    date_controle = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valeur = db.Column(db.String(100), nullable=False)
    unite = db.Column(db.String(20))
    conforme = db.Column(db.Boolean, default=True)
    operateur = db.Column(db.String(100))
    commentaire = db.Column(db.Text)
    action_entreprise = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class Prp(db.Model):
    __tablename__ = 'haccp_prp'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    categorie = db.Column(db.String(50), nullable=False)
    element = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    frequence = db.Column(db.String(100))
    responsable = db.Column(db.String(100))
    procedure_reference = db.Column(db.String(200))
    type_prp = db.Column(db.String(20), default='generic')  # 'generic' | 'operational'
    processus_id = db.Column(db.Integer, db.ForeignKey('haccp_processus.id'), nullable=True)
    danger_id = db.Column(db.Integer, db.ForeignKey('haccp_analyse_danger.id'), nullable=True)
    limite_critique = db.Column(db.String(200))
    methode_surveillance = db.Column(db.Text)
    frequence_surveillance = db.Column(db.String(100))
    action_corrective = db.Column(db.Text)
    verifie_le = db.Column(db.Date)
    prochaine_verification = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    processus = db.relationship('ProcessusHaccp', foreign_keys=[processus_id])
    danger = db.relationship('AnalyseDanger', foreign_keys=[danger_id])


class EnregistrementOprp(db.Model):
    __tablename__ = 'haccp_enregistrement_oprp'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    oprp_id = db.Column(db.Integer, db.ForeignKey('haccp_prp.id'), nullable=False)
    date_controle = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valeur = db.Column(db.String(100), nullable=False)
    unite = db.Column(db.String(20))
    conforme = db.Column(db.Boolean, default=True)
    operateur = db.Column(db.String(100))
    commentaire = db.Column(db.Text)
    action_entreprise = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    oprp = db.relationship('Prp', backref=db.backref('enregistrements_oprp', lazy='dynamic', cascade='all, delete-orphan'))


class TracabiliteLot(db.Model):
    __tablename__ = 'haccp_tracabilite_lot'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    code_lot = db.Column(db.String(100), nullable=False)
    produit_nom = db.Column(db.String(200))
    date_fabrication = db.Column(db.Date)
    date_expiration = db.Column(db.Date)
    quantite = db.Column(db.String(50))
    fournisseur = db.Column(db.String(200))
    lot_fournisseur = db.Column(db.String(100))
    matieres_utilisees = db.Column(db.Text)
    statut = db.Column(db.String(20), default='disponible')
    notes = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class RappelProduit(db.Model):
    __tablename__ = 'haccp_rappel'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    reference = db.Column(db.String(50))
    produit = db.Column(db.String(200))
    lot = db.Column(db.String(100))
    date_rappel = db.Column(db.Date, nullable=False, default=date.today)
    motif = db.Column(db.Text, nullable=False)
    gravite = db.Column(db.String(20))
    actions_menées = db.Column(db.Text)
    client_notifie = db.Column(db.Boolean, default=False)
    autorite_notifiee = db.Column(db.Boolean, default=False)
    statut = db.Column(db.String(20), default='en_cours')
    cloture_le = db.Column(db.Date)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')



