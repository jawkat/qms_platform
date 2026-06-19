from app import db
from datetime import datetime, date


class Competence(db.Model):
    __tablename__ = 'competence'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    domaine = db.Column(db.String(20), default='qualite')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')


class FormationParticipant(db.Model):
    __tablename__ = 'formation_participant'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formation_partage.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    evaluation_score = db.Column(db.Float)
    evaluation_commentaire = db.Column(db.Text)
    certifie = db.Column(db.Boolean, default=False)
    date_certification = db.Column(db.Date)
    date_expiration_certification = db.Column(db.Date)
    statut = db.Column(db.String(20), default='inscrit')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    formation = db.relationship('Formation', backref='participants_list')
    utilisateur = db.relationship('Utilisateur')
