from app.extensions import db
from .base import BaseModel


class AspectEnvironnemental(BaseModel):
    __tablename__ = 'env_aspect'
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50))
    impact = db.Column(db.Text)
    gravite = db.Column(db.String(20), default='moyenne')
    maitrise = db.Column(db.Text)
    responsable = db.Column(db.String(100))
    significatif = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer)
    frequence = db.Column(db.String(50))
    statut = db.Column(db.String(20), default='identifie')
    
    entreprise = db.relationship('Entreprise')


class SuiviEnvironnemental(BaseModel):
    __tablename__ = 'env_suivi'
    aspect_id = db.Column(db.Integer, db.ForeignKey('env_aspect.id'), nullable=False)
    date_mesure = db.Column(db.DateTime, nullable=False)
    valeur = db.Column(db.Float)
    unite = db.Column(db.String(20))
    conforme = db.Column(db.Boolean)
    commentaire = db.Column(db.Text)
    
    entreprise = db.relationship('Entreprise')
    aspect = db.relationship('AspectEnvironnemental', backref='suivis')
