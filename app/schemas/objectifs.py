from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.qualite import ObjectifQualite

class ObjectifQualiteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectifQualite
        load_instance = True
        include_fk = True
    
    progression = fields.Integer(dump_only=True)
    pilote_name = fields.Function(
        lambda obj: f"{obj.pilote.prenom} {obj.pilote.nom}" if obj.pilote else "",
        dump_only=True
    )
