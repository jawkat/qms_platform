from app.extensions import db
from .base import BaseModel


class PlanUrgence(BaseModel):
    __tablename__ = 'plan_urgence'
    nom = db.Column(db.String(200), nullable=False)
    type_urgence = db.Column(db.String(50))  # incendie, accident, pollution, autre
    description = db.Column(db.Text)
    procedures = db.Column(db.Text)
    contacts_cles = db.Column(db.JSON, default=list)  # [{nom, telephone, role}]
    materiel = db.Column(db.Text)
    date_derniere_revu = db.Column(db.Date)
    date_prochaine_revu = db.Column(db.Date)
    statut = db.Column(db.String(20), default='actif')
    
    entreprise = db.relationship('Entreprise')


class ExerciceEvacuation(BaseModel):
    __tablename__ = 'exercice_evacuation'
    plan_urgence_id = db.Column(db.Integer, db.ForeignKey('plan_urgence.id'))
    date_exercice = db.Column(db.DateTime, nullable=False)
    lieu = db.Column(db.String(200))
    responsable = db.Column(db.String(100))
    participants = db.Column(db.Integer)
    duree_minutes = db.Column(db.Integer)
    resultat = db.Column(db.Text)
    observations = db.Column(db.Text)
    ameliorations = db.Column(db.Text)
    statut = db.Column(db.String(20), default='planifie')  # planifie, realise
    
    entreprise = db.relationship('Entreprise')
    plan = db.relationship('PlanUrgence')


class MainCourante(BaseModel):
    __tablename__ = 'main_courante'
    date_evenement = db.Column(db.DateTime, nullable=False)
    type_evenement = db.Column(db.String(50))  # incident, urgence, exercice, info
    description = db.Column(db.Text, nullable=False)
    lieu = db.Column(db.String(200))
    declares_par = db.Column(db.String(100))
    actions_entreprises = db.Column(db.Text)
    statut = db.Column(db.String(20), default='ouvert')  # ouvert, en_cours, cloture
    
    entreprise = db.relationship('Entreprise')
