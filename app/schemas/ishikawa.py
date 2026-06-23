from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.ishikawa import AnalyseIshikawa, CauseIshikawa

class CauseIshikawaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CauseIshikawa
        load_instance = True
        include_fk = True

class AnalyseIshikawaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AnalyseIshikawa
        load_instance = True
        include_fk = True
    
    entreprise_id = fields.Integer(required=False, load_default=None)
    
    auteur_name = fields.Function(
        lambda obj: f"{obj.auteur.prenom} {obj.auteur.nom}" if obj.auteur else "",
        dump_only=True
    )
    causes = fields.Nested(CauseIshikawaSchema, many=True, dump_only=True)
