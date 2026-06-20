from app.extensions import db
from .base import TimestampMixin
from datetime import datetime, date

class Entreprise(db.Model, TimestampMixin):
    __tablename__ = 'entreprise'
    
    nom = db.Column(db.String(100), nullable=False)
    taille = db.Column(db.String(20), default='PME')
    pays = db.Column(db.String(50), default='Maroc')
    adresse = db.Column(db.Text)
    date_inscription = db.Column(db.Date, default=date.today)
    modules_actifs = db.Column(db.JSON, default=lambda: ['hse'])
    abonnement_type = db.Column(db.String(50), default='trial')
    abonnement_prochaine_echeance = db.Column(db.Date)
    abonnement_paye = db.Column(db.Boolean, default=False)
    statut = db.Column(db.String(20), default='Actif')
    motif_suspension = db.Column(db.String(50))
    date_dernier_paiement = db.Column(db.Date)
    montant_annuel_mad = db.Column(db.Numeric(10, 2))
    contact_facturation_email = db.Column(db.String(120))
    notes_facturation = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    periode_essai_jours = db.Column(db.Integer, default=14)
    date_debut_essai = db.Column(db.DateTime)

    utilisateurs = db.relationship('Utilisateur', back_populates='entreprise')
    secteurs = db.relationship('Secteur', secondary='entreprise_secteur', back_populates='entreprises')
    historique_paiements = db.relationship('HistoriquePaiement', back_populates='entreprise')


class Secteur(db.Model, TimestampMixin):
    __tablename__ = 'secteur'
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    entreprises = db.relationship('Entreprise', secondary='entreprise_secteur', back_populates='secteurs')
    textes = db.relationship('TexteReglementaire', secondary='texte_secteur', back_populates='secteurs')


class EntrepriseSecteur(db.Model):
    __tablename__ = 'entreprise_secteur'
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), primary_key=True)
    secteur_id = db.Column(db.Integer, db.ForeignKey('secteur.id'), primary_key=True)


class SubscriptionPlan(db.Model, TimestampMixin):
    __tablename__ = 'subscription_plan'
    plan_key = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    max_users = db.Column(db.Integer, default=2)
    price_mad = db.Column(db.Integer, default=0)
    max_documents = db.Column(db.Integer, default=200)
    max_open_actions = db.Column(db.Integer, default=80)
    max_storage_mb = db.Column(db.Integer, default=512)
    trial_days = db.Column(db.Integer, default=14)
    features = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)


class HistoriquePaiement(db.Model, TimestampMixin):
    __tablename__ = 'historique_paiement'
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    date_paiement = db.Column(db.Date, nullable=False)
    montant_mad = db.Column(db.Numeric(10, 2), nullable=False)
    methode_paiement = db.Column(db.String(50))
    reference_externe = db.Column(db.String(100))
    statut_paiement = db.Column(db.String(20))
    notes = db.Column(db.Text)
    enregistre_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    entreprise = db.relationship('Entreprise', back_populates='historique_paiements')
