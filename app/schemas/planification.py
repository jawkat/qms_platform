from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.planification import EvenementPlanification

class EvenementPlanificationSchema(AutoSchema):
    class Meta:
        model = EvenementPlanification
        load_instance = True
        include_fk = True
    
    pilote_name = fields.Function(
        lambda obj: f"{obj.pilote.prenom} {obj.pilote.nom}" if obj.pilote else "",
        dump_only=True
    )
