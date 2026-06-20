from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.reunions import Reunion, CompteRendu, ActionReunion

class ActionReunionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ActionReunion
        load_instance = True
        include_fk = True
    
    responsable_name = fields.Function(
        lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else "",
        dump_only=True
    )

class CompteRenduSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CompteRendu
        load_instance = True
        include_fk = True
    
    actions = fields.Nested(ActionReunionSchema, many=True, dump_only=True)

class ReunionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Reunion
        load_instance = True
        include_fk = True
    
    compte_rendu = fields.Nested(CompteRenduSchema, dump_only=True)
