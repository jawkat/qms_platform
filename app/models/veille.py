from app.extensions import db
from .base import TimestampMixin


class SourceReglementaire(db.Model, TimestampMixin):
    __tablename__ = 'source_reglementaire'
    nom = db.Column(db.String(100))
    url = db.Column(db.String(255))
    type_source = db.Column(db.String(50))
    contact = db.Column(db.String(100))
    veilles = db.relationship('Veille', back_populates='source')


class Veille(db.Model, TimestampMixin):
    __tablename__ = 'veille'
    texte_id = db.Column(db.Integer, db.ForeignKey('texte_reglementaire.id'))
    source_id = db.Column(db.Integer, db.ForeignKey('source_reglementaire.id'))
    date_detection = db.Column(db.Date)
    statut = db.Column(db.String(50))
    resume = db.Column(db.Text)
    lien_source = db.Column(db.String(255))
    
    texte = db.relationship('TexteReglementaire')
    source = db.relationship('SourceReglementaire', back_populates='veilles')
