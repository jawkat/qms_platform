import uuid
from datetime import datetime
from app import db


class Disponibilite(db.Model):
    __tablename__ = 'disponibilite'
    id = db.Column(db.Integer, primary_key=True)
    jour_semaine = db.Column(db.Integer, nullable=False)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    actif = db.Column(db.Boolean, default=True)


class CreneauDemo(db.Model):
    __tablename__ = 'creneau_demo'
    id = db.Column(db.Integer, primary_key=True)
    date_heure_debut = db.Column(db.DateTime, nullable=False)
    duree_minutes = db.Column(db.Integer, default=30)
    email_contact = db.Column(db.String(120), nullable=False)
    nom_contact = db.Column(db.String(100), nullable=False)
    entreprise = db.Column(db.String(100), nullable=True)
    statut = db.Column(db.String(20), nullable=False, default='reserve')
    token_annulation = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    lien_visio = db.Column(db.String(255), nullable=True)
    nb_rappels = db.Column(db.Integer, default=0)
    ticket = db.relationship('Ticket', foreign_keys=[ticket_id])
