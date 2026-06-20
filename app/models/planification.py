from app.extensions import db
from .base import BaseModel


class EvenementPlanification(BaseModel):
    __tablename__ = 'planif_evenement'
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date_debut = db.Column(db.DateTime, nullable=False)
    date_fin = db.Column(db.DateTime)
    type_evenement = db.Column(db.String(50))  # audit, formation, réunion, maintenance
    pilote_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='planifie')
    
    entreprise = db.relationship('Entreprise')
    pilote = db.relationship('Utilisateur')
