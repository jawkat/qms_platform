from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.rh_qhse import EmployeQHSE

class EmployeQHSESchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EmployeQHSE
        load_instance = True
        include_fk = True
    
    utilisateur_name = fields.Function(
        lambda obj: f"{obj.utilisateur.prenom} {obj.utilisateur.nom}" if obj.utilisateur else "",
        dump_only=True
    )
