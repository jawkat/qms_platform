from app import db
from datetime import datetime


class AnalyseIshikawa(db.Model):
    __tablename__ = 'analyse_ishikawa'
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    source_type = db.Column(db.String(30))
    source_id = db.Column(db.Integer)
    description_effet = db.Column(db.Text, nullable=False)
    date_analyse = db.Column(db.Date, nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    entreprise = db.relationship('Entreprise')
    auteur = db.relationship('Utilisateur')
    causes = db.relationship('CauseIshikawa', backref='analyse', lazy='dynamic',
                             cascade='all, delete-orphan')


class CauseIshikawa(db.Model):
    __tablename__ = 'cause_ishikawa'
    id = db.Column(db.Integer, primary_key=True)
    analyse_id = db.Column(db.Integer, db.ForeignKey('analyse_ishikawa.id'), nullable=False)
    categorie = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
