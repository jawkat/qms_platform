from app import db
from datetime import datetime


class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    domaine = db.Column(db.String(20), default='hse', nullable=False, index=True)
    type = db.Column(db.String(50))
    date_audit = db.Column(db.Date)
    auditeur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    resultat_global = db.Column(db.String(50))
    commentaire = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    entreprise = db.relationship('Entreprise')
    auditeur = db.relationship('Utilisateur')
    observations = db.relationship('AuditObservation', back_populates='audit')


class AuditObservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.Integer, db.ForeignKey('audit.id'))
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    constat = db.Column(db.Text)
    niveau_conformite = db.Column(db.String(50))
    action_recommandee = db.Column(db.Text)

    audit = db.relationship('Audit', back_populates='observations')
    texte = db.relationship('TexteReglementaire')
    article = db.relationship('Article')
