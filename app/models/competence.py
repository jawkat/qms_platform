from app.extensions import db
from .base import BaseModel, TimestampMixin


class Competence(BaseModel):
    __tablename__ = 'competence'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    domaine = db.Column(db.String(20), default='qualite')
    
    entreprise = db.relationship('Entreprise')


class EmployeCompetence(BaseModel):
    __tablename__ = 'employe_competence'
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    competence_id = db.Column(db.Integer, db.ForeignKey('competence.id'), nullable=False)
    niveau_requis = db.Column(db.Integer, default=1)
    niveau_actuel = db.Column(db.Integer, default=0)
    date_evaluation = db.Column(db.Date)
    evalue_par_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    notes = db.Column(db.Text)
    
    utilisateur = db.relationship('Utilisateur', foreign_keys=[utilisateur_id])
    competence = db.relationship('Competence')
    evalue_par = db.relationship('Utilisateur', foreign_keys=[evalue_par_id])


class FormationParticipant(db.Model, TimestampMixin):
    __tablename__ = 'formation_participant'
    formation_id = db.Column(db.Integer, db.ForeignKey('formation_partage.id'), nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    evaluation_score = db.Column(db.Float)
    evaluation_commentaire = db.Column(db.Text)
    certifie = db.Column(db.Boolean, default=False)
    date_certification = db.Column(db.Date)
    date_expiration_certification = db.Column(db.Date)
    statut = db.Column(db.String(20), default='inscrit')
    
    formation = db.relationship('Formation', backref='participants_list')
    utilisateur = db.relationship('Utilisateur')
