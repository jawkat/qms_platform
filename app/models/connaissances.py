from app.extensions import db
from .base import BaseModel


class REX(BaseModel):
    __tablename__ = 'rex'
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))  # incident, amelioration, best_practice, lecon
    contexte = db.Column(db.Text)
    causes = db.Column(db.Text)
    actions_menees = db.Column(db.Text)
    resultats = db.Column(db.Text)
    lecons_apprises = db.Column(db.Text)
    auteur = db.Column(db.String(100))
    date_rex = db.Column(db.Date)
    statut = db.Column(db.String(20), default='brouillon')  # brouillon, publie
    
    entreprise = db.relationship('Entreprise')


class FAQ(BaseModel):
    __tablename__ = 'faq'
    question = db.Column(db.String(500), nullable=False)
    reponse = db.Column(db.Text, nullable=False)
    categorie = db.Column(db.String(50))
    vue_count = db.Column(db.Integer, default=0)
    utile_count = db.Column(db.Integer, default=0)
    
    entreprise = db.relationship('Entreprise')
