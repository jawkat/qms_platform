from app.extensions import db
from .base import TimestampMixin


class EvaluationFournisseur(db.Model, TimestampMixin):
    __tablename__ = 'evaluation_fournisseur'
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur_partage.id'), nullable=False)
    date_evaluation = db.Column(db.Date, nullable=False)
    evaluateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    score_global = db.Column(db.Float)
    commentaire = db.Column(db.Text)
    
    fournisseur = db.relationship('Fournisseur', backref='evaluations')
    evaluateur = db.relationship('Utilisateur')


class HistoriqueFournisseur(db.Model, TimestampMixin):
    __tablename__ = 'historique_fournisseur'
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseur_partage.id'), nullable=False)
    type_evenement = db.Column(db.String(30), nullable=False)
    date_evenement = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    score = db.Column(db.Float)
    auteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    
    fournisseur = db.relationship('Fournisseur', backref='historique')
    auteur = db.relationship('Utilisateur')
