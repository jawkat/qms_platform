from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from datetime import datetime


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    module = db.Column(db.String(50))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True)
    autorise = db.Column(db.Boolean, default=True)
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', 'entreprise_id', name='uq_role_perm_entreprise'),
    )


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    est_systeme = db.Column(db.Boolean, default=False)
    personnalisable = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    cree_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    createur = db.relationship('Utilisateur', foreign_keys=[cree_par])


class EntrepriseRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permissions_personnalisees = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class Utilisateur(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255))
    actif = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'))
    telephone = db.Column(db.String(20))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    dernier_acces = db.Column(db.DateTime)

    role = db.relationship('Role', foreign_keys=[role_id])
    entreprise = db.relationship('Entreprise', back_populates='utilisateurs')

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def has_permission(self, permission_code, entreprise_id=None):
        if not self.role:
            return False
        if self.role.est_systeme:
            return True
        eid = entreprise_id or self.entreprise_id
        perm = Permission.query.filter_by(code=permission_code).first()
        if not perm:
            return False
        rp = RolePermission.query.filter_by(
            role_id=self.role_id, permission_id=perm.id,
            entreprise_id=eid, autorise=True
        ).first()
        return rp is not None

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except Exception:
            return None
        return db.session.get(Utilisateur, user_id)

    def get_id(self):
        return str(self.id)
