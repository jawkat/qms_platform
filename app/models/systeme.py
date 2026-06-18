from app import db
from datetime import datetime


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)
    lu = db.Column(db.Boolean, default=False)


class JournalSecurite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    type_action = db.Column(db.String(50))
    adresse_ip = db.Column(db.String(50))
    navigateur = db.Column(db.String(200))
    date_action = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)
    resolu = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
