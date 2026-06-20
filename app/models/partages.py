from app.extensions import db
from datetime import date
from .base import BaseModel


class Fournisseur(BaseModel):
    __tablename__ = 'fournisseur_partage'
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
    pays = db.Column(db.String(50))
    delai_livraison = db.Column(db.String(50))
    taux_defaut = db.Column(db.Float, default=0)
    score_qualite = db.Column(db.Float, default=0)
    score_delai = db.Column(db.Float, default=0)
    score_prix = db.Column(db.Float, default=0)
    score_global = db.Column(db.Float, default=0)
    commentaire_score = db.Column(db.Text)
    
    entreprise = db.relationship('Entreprise')

    @property
    def produit_fourni(self):
        return self.produit

    @produit_fourni.setter
    def produit_fourni(self, value):
        self.produit = value

    def calculer_score_global(self):
        self.score_global = round(
            (self.score_qualite or 0) * 0.4 +
            (self.score_delai or 0) * 0.3 +
            (self.score_prix or 0) * 0.3, 1
        )
        return self.score_global


class Formation(BaseModel):
    __tablename__ = 'formation_partage'
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
    
    entreprise = db.relationship('Entreprise')


class Reclamation(BaseModel):
    __tablename__ = 'reclamation_partage'
    domaine = db.Column(db.String(20), default='qualite')
    date_reclamation = db.Column(db.Date, nullable=False, default=date.today)
    client = db.Column(db.String(100), nullable=False)
    produit = db.Column(db.String(200))
    lot = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    type_reclamation = db.Column(db.String(50))
    severite = db.Column(db.String(20), default='moyenne')
    categorie = db.Column(db.String(50))
    action = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    cloture_le = db.Column(db.Date)
    statut = db.Column(db.String(20), default='ouverte')
    investigation = db.Column(db.Text)
    cause_racine = db.Column(db.Text)
    action_corrective_id = db.Column(db.Integer, db.ForeignKey('action_corrective.id'))
    
    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur', foreign_keys=[responsable_id])
