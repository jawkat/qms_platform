from app.extensions import db
from .base import BaseModel, TimestampMixin


class AnalyseIshikawa(BaseModel):
    __tablename__ = 'analyse_ishikawa'
    source_type = db.Column(db.String(30))
    source_id = db.Column(db.Integer)
    description_effet = db.Column(db.Text, nullable=False)
    date_analyse = db.Column(db.Date, nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    entreprise = db.relationship('Entreprise')
    auteur = db.relationship('Utilisateur')
    causes = db.relationship('CauseIshikawa', backref='analyse', lazy='dynamic',
                             cascade='all, delete-orphan')


class CauseIshikawa(db.Model, TimestampMixin):
    __tablename__ = 'cause_ishikawa'
    analyse_id = db.Column(db.Integer, db.ForeignKey('analyse_ishikawa.id'), nullable=False)
    categorie = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
