from app import db
from datetime import date, datetime


class Fournisseur(db.Model):
    __tablename__ = 'fournisseur_partage'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='qualite')
    nom = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(20))
    produit = db.Column(db.String(200))
    certification = db.Column(db.String(200))
    evaluation = db.Column(db.Integer)
    qualification = db.Column(db.String(20), default='non_qualifie')
    date_qualification = db.Column(db.Date)
    certificats = db.Column(db.Text)
    dernier_audit = db.Column(db.Date)
    prochain_audit = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')

    @property
    def produit_fourni(self):
        return self.produit

    @produit_fourni.setter
    def produit_fourni(self, value):
        self.produit = value


class Formation(db.Model):
    __tablename__ = 'formation_partage'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='qualite')
    titre = db.Column(db.String(200), nullable=False)
    theme = db.Column(db.String(100))
    formateur = db.Column(db.String(100))
    participants = db.Column(db.Text)
    date_formation = db.Column(db.Date)
    duree_heures = db.Column(db.Float)
    type_formation = db.Column(db.String(20), default='interne')
    evaluation = db.Column(db.Text)
    objectifs = db.Column(db.Text)
    prerequis = db.Column(db.Text)
    cout = db.Column(db.Numeric(10, 2))
    statut = db.Column(db.String(20), default='planifiee')
    annee = db.Column(db.Integer)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class Reclamation(db.Model):
    __tablename__ = 'reclamation_partage'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    domaine = db.Column(db.String(20), default='qualite')
    date_reclamation = db.Column(db.Date, nullable=False, default=date.today)
    client = db.Column(db.String(100), nullable=False)
    produit = db.Column(db.String(200))
    lot = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    type_reclamation = db.Column(db.String(50))
    action = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    cloture_le = db.Column(db.Date)
    statut = db.Column(db.String(20), default='ouverte')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur')
