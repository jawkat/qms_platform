from app import db
from datetime import datetime


class EvaluationFournisseur(db.Model):
    __tablename__ = 'evaluation_fournisseur'
    id = db.Column(db.Integer, primary_key=True)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur_partage.id'), nullable=False)
    date_evaluation = db.Column(db.Date, nullable=False)
    evaluateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    score_global = db.Column(db.Float)
    commentaire = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    fournisseur = db.relationship('Fournisseur', backref='evaluations')
    evaluateur = db.relationship('Utilisateur')


class HistoriqueFournisseur(db.Model):
    __tablename__ = 'historique_fournisseur'
    id = db.Column(db.Integer, primary_key=True)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur_partage.id'), nullable=False)
    type_evenement = db.Column(db.String(30), nullable=False)
    date_evenement = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    score = db.Column(db.Float)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    fournisseur = db.relationship('Fournisseur', backref='historique')
    auteur = db.relationship('Utilisateur')
