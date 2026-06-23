from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.reunions import Reunion, CompteRendu, ActionReunion

class ActionReunionSchema(AutoSchema):
    class Meta:
        model = ActionReunion
        load_instance = True
        include_fk = True
    
    responsable_name = fields.Function(
        lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else "",
        dump_only=True
    )

class CompteRenduSchema(AutoSchema):
    class Meta:
        model = CompteRendu
        load_instance = True
        include_fk = True
    
    actions = fields.Nested(ActionReunionSchema, many=True, dump_only=True)

class ReunionSchema(AutoSchema):
    class Meta:
        model = Reunion
        load_instance = True
        include_fk = True
    
    compte_rendu = fields.Nested(CompteRenduSchema, dump_only=True)
