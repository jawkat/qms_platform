from app import db
from datetime import datetime


class ObligationReglementaire(db.Model):
    __tablename__ = 'obligation_reglementaire'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    obligation_description = db.Column(db.Text, nullable=False)
    date_echeance = db.Column(db.Date, nullable=False)
    periodicite = db.Column(db.String(20), default='ponctuelle')
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='a_faire')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    texte = db.relationship('TexteReglementaire')
    responsable = db.relationship('Utilisateur')
