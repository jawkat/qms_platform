from app.extensions import db
from .base import TimestampMixin


class Notification(db.Model, TimestampMixin):
    __tablename__ = 'notification'
    type = db.Column(db.String(50))
    message = db.Column(db.Text)
    categorie = db.Column(db.String(50), default='general') # ex: 'hse', 'ged', 'audit'
    urgence = db.Column(db.String(20), default='normale') # 'basse', 'normale', 'haute', 'critique'
    entite_type = db.Column(db.String(50)) # ex: 'accident', 'document'
    entite_id = db.Column(db.Integer)      # ID de l'accident ou du doc
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    date_envoi = db.Column(db.DateTime, default=db.func.now())
    lu = db.Column(db.Boolean, default=False)


class JournalSecurite(db.Model, TimestampMixin):
    __tablename__ = 'journal_securite'
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    type_action = db.Column(db.String(50))
    adresse_ip = db.Column(db.String(50))
    navigateur = db.Column(db.String(200))
    date_action = db.Column(db.DateTime, default=db.func.now())
    details = db.Column(db.JSON)
    resolu = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))


class TacheSysteme(db.Model, TimestampMixin):
    __tablename__ = 'tache_systeme'
    type_tache = db.Column(db.String(50))
    date_execution = db.Column(db.DateTime)
    statut = db.Column(db.String(50))
    resultat = db.Column(db.Text)


class NotificationPreference(db.Model, TimestampMixin):
    __tablename__ = 'notification_preference'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    categorie = db.Column(db.String(50), nullable=False) # ex: 'ged', 'hse', 'audit', 'systeme'
    app_enabled = db.Column(db.Boolean, default=True)
    email_enabled = db.Column(db.Boolean, default=True)
    frequence = db.Column(db.String(20), default='immediat') # 'immediat', 'quotidien', 'hebdo'

    __table_args__ = (
        db.UniqueConstraint('utilisateur_id', 'categorie', name='uq_user_notif_cat'),
    )
