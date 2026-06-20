from app.extensions import db
from datetime import datetime

class TimestampMixin:
    """
    Mixin pour ajouter id, date_creation et date_modification.
    """
    id = db.Column(db.Integer, primary_key=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BaseModel(db.Model, TimestampMixin):
    """
    Classe de base pour tous les modèles multi-tenant.
    """
    __abstract__ = True

    @db.declared_attr
    def entreprise_id(cls):
        return db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False, index=True)

    # Relation vers l'entreprise (optionnelle car certains modèles l'utilisent différemment)
    # On laisse les modèles enfants définir leurs relations spécifiques si besoin

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
