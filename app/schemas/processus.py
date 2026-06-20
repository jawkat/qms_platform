from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.processus import Processus, IndicateurProcessus

class ProcessusSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Processus
        load_instance = True
        include_fk = True

    proprietaire_name = fields.Function(
        lambda obj: f"{obj.proprietaire.prenom} {obj.proprietaire.nom}" if obj.proprietaire else "",
        dump_only=True
    )

class IndicateurProcessusSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IndicateurProcessus
        load_instance = True
        include_fk = True
