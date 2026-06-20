import uuid
from app.extensions import db
from .base import TimestampMixin


class Disponibilite(db.Model, TimestampMixin):
    __tablename__ = 'disponibilite'
    jour_semaine = db.Column(db.Integer, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    actif = db.Column(db.Boolean, default=True)


class CreneauDemo(db.Model, TimestampMixin):
    __tablename__ = 'creneau_demo'
    date_heure_debut = db.Column(db.DateTime, nullable=False)
    duree_minutes = db.Column(db.Integer, default=30)
    email_contact = db.Column(db.String(120), nullable=False)
    nom_contact = db.Column(db.String(100), nullable=False)
    entreprise = db.Column(db.String(100), nullable=True)
    statut = db.Column(db.String(20), nullable=False, default='reserve')
    token_annulation = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    lien_visio = db.Column(db.String(255), nullable=True)
    nb_rappels = db.Column(db.Integer, default=0)
    
    ticket = db.relationship('Ticket', foreign_keys=[ticket_id])
