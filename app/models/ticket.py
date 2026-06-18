from app import db
from datetime import datetime


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(30), unique=True, nullable=False)
    type = db.Column(db.String(30), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(20), nullable=False)
    email_contact = db.Column(db.String(120))
    nom_contact = db.Column(db.String(100))
    telephone = db.Column(db.String(30))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    cree_par_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_dernier_message = db.Column(db.DateTime)
    date_fermeture = db.Column(db.DateTime)

    messages = db.relationship('MessageTicket', back_populates='ticket', cascade='all, delete-orphan')


class MessageTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    auteur_type = db.Column(db.String(20), nullable=False)
    auteur_nom = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    est_interne = db.Column(db.Boolean, default=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship('Ticket', back_populates='messages')
