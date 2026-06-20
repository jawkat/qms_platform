from app.extensions import db
from .base import BaseModel
from datetime import date


class NonConformite(BaseModel):
    __tablename__ = 'nonconformite'
    domaine = db.Column(db.String(20), nullable=False)

    reference = db.Column(db.String(50))
    date_nc = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=False)
    action_corrective = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    statut = db.Column(db.String(20), default='ouverte')
    gravite = db.Column(db.String(20), default='majeur')

    produit_processus = db.Column(db.String(200))
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation_article.id'))

    source = db.Column(db.String(50))
    cause = db.Column(db.Text)
    delai = db.Column(db.Date)
    cloture_le = db.Column(db.Date)
    efficacite_verifiee = db.Column(db.Boolean, default=False)

    validee_par_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_validation_cloture = db.Column(db.Date)

    entreprise = db.relationship('Entreprise')
    responsable = db.relationship('Utilisateur', foreign_keys=[responsable_id])
    validee_par = db.relationship('Utilisateur', foreign_keys=[validee_par_id])
    evaluation = db.relationship('EvaluationArticle')
