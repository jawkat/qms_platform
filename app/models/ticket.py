from app.extensions import db
from .base import BaseModel, TimestampMixin
import secrets


class Ticket(db.Model, TimestampMixin):
    __tablename__ = 'ticket'
    reference = db.Column(db.String(30), unique=True, nullable=False)
    type = db.Column(db.String(30), nullable=False)
    sujet = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(20), nullable=False)
    email_contact = db.Column(db.String(120))
    nom_contact = db.Column(db.String(100))
    telephone = db.Column(db.String(30))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    cree_par_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_dernier_message = db.Column(db.DateTime)
    date_fermeture = db.Column(db.DateTime)

    messages = db.relationship('MessageTicket', back_populates='ticket', cascade='all, delete-orphan')

    @staticmethod
    def generer_reference():
        from datetime import date
        suffix = secrets.token_hex(3).upper()
        return f"TKT-{date.today().strftime('%Y%m%d')}-{suffix}"

    def nb_messages(self):
        return len(self.messages) if self.messages else 0


class MessageTicket(db.Model, TimestampMixin):
    __tablename__ = 'message_ticket'
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    auteur_type = db.Column(db.String(20), nullable=False)
    auteur_nom = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    est_interne = db.Column(db.Boolean, default=False)
    date_envoi = db.Column(db.DateTime, default=db.func.now())

    ticket = db.relationship('Ticket', back_populates='messages')
