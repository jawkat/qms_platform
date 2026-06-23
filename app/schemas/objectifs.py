from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.qualite import ObjectifQualite

class ObjectifQualiteSchema(AutoSchema):
    class Meta:
        model = ObjectifQualite
        load_instance = True
        include_fk = True
    
    progression = fields.Integer(dump_only=True)
    pilote_name = fields.Function(
        lambda obj: f"{obj.pilote.prenom} {obj.pilote.nom}" if obj.pilote else "",
        dump_only=True
    )
