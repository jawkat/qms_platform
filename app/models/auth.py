from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from datetime import datetime
from .base import TimestampMixin, BaseModel

class Permission(db.Model, TimestampMixin):
    __tablename__ = 'permission'
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    module = db.Column(db.String(50))

class RolePermission(db.Model, TimestampMixin):
    __tablename__ = 'role_permission'
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True)
    autorise = db.Column(db.Boolean, default=True)
    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', 'entreprise_id', name='uq_role_perm_entreprise'),
    )

class Role(db.Model, TimestampMixin):
    __tablename__ = 'role'
    nom = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text)
    est_systeme = db.Column(db.Boolean, default=False)
    personnalisable = db.Column(db.Boolean, default=True)
    cree_par = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    createur = db.relationship('Utilisateur', foreign_keys=[cree_par])

class EntrepriseRole(BaseModel):
    __tablename__ = 'entreprise_role'
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permissions_personnalisees = db.Column(db.Boolean, default=False)

class Utilisateur(UserMixin, db.Model, TimestampMixin):
    __tablename__ = 'utilisateur'
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255))
    actif = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    entreprise_id = db.Column(db.Integer, db.ForeignKey('entreprise.id'), nullable=True) # Nullable for sys admins
    telephone = db.Column(db.String(20))
    dernier_acces = db.Column(db.DateTime)

    role = db.relationship('Role', foreign_keys=[role_id])
    entreprise = db.relationship('Entreprise', back_populates='utilisateurs')

    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        if not self.mot_de_passe:
            return False
        return check_password_hash(self.mot_de_passe, password)

    @property
    def is_manager(self):
        return self.role and self.role.nom == 'Manager'

    def has_permission(self, permission_code, entreprise_id=None):
        if not self.role:
            return False
        if self.role.est_systeme:
            return True
        # Manager bypass: grant all active-module permissions
        # except admin-only features (textes CRUD, system admin)
        if self.is_manager:
            if permission_code.startswith('admin.'):
                return False
            if permission_code == 'textes.modifier':
                return False
            eid = entreprise_id or self.entreprise_id
            if eid:
                from app.models.entreprise import Entreprise
                entreprise = db.session.get(Entreprise, eid)
                if entreprise:
                    return True
        eid = entreprise_id or self.entreprise_id
        perm = Permission.query.filter_by(code=permission_code).first()
        if not perm:
            return False
        rp = RolePermission.query.filter(
            RolePermission.role_id == self.role_id,
            RolePermission.permission_id == perm.id,
            db.or_(RolePermission.entreprise_id == eid, RolePermission.entreprise_id.is_(None)),
            RolePermission.autorise == True
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
        return db.session.get(Utilisateur, int(user_id))

    def get_id(self):
        return str(self.id)
