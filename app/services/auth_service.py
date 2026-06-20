from app.services.base import BaseService
from app.models.auth import Utilisateur, Role, Permission
from app.extensions import db

class AuthService(BaseService):
    model = Utilisateur

    @classmethod
    def register_user(cls, nom, prenom, email, password, entreprise_id=None, role_nom='employe'):
        role = Role.query.filter_by(nom=role_nom).first()
        user = cls.model(
            nom=nom,
            prenom=prenom,
            email=email,
            entreprise_id=entreprise_id,
            role_id=role.id if role else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def get_user_by_email(cls, email):
        return cls.model.query.filter_by(email=email).first()

    @classmethod
    def update_last_access(cls, user_id):
        user = cls.get_by_id(user_id)
        if user:
            from datetime import datetime
            user.dernier_acces = datetime.utcnow()
            db.session.commit()
