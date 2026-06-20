from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.auth import Utilisateur, Role, Permission
from app.models.systeme import Notification

class PermissionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Permission
        load_instance = True

class RoleSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        load_instance = True
    
    permissions = fields.List(fields.Nested(PermissionSchema))

class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Utilisateur
        load_instance = True
        include_fk = True
        exclude = ('password_hash',) # NEVER expose password hash
    
    roles_list = fields.Function(lambda obj: [r.nom for r in obj.roles], dump_only=True)

class NotificationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Notification
        load_instance = True
        include_fk = True
