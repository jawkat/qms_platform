from app import db
from datetime import datetime


class SourceReglementaire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    url = db.Column(db.String(255))
    type_source = db.Column(db.String(50))
    contact = db.Column(db.String(100))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    veilles = db.relationship('Veille', back_populates='source')


class Veille(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('source_reglementaire.id'))
    date_detection = db.Column(db.Date)
    statut = db.Column(db.String(50))
    resume = db.Column(db.Text)
    lien_source = db.Column(db.String(255))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    texte = db.relationship('TexteReglementaire')
    source = db.relationship('SourceReglementaire', back_populates='veilles')
