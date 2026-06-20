from app.extensions import db
from .base import BaseModel


class ObligationReglementaire(BaseModel):
    __tablename__ = 'obligation_reglementaire'
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    obligation_description = db.Column(db.Text, nullable=False)
    date_echeance = db.Column(db.Date, nullable=False)
    periodicite = db.Column(db.String(20), default='ponctuelle')
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='a_faire')
    
    entreprise = db.relationship('Entreprise')
    texte = db.relationship('TexteReglementaire')
    responsable = db.relationship('Utilisateur')
