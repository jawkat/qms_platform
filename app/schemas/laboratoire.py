from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.laboratoire import PlanAnalyse, Echantillon, ResultatAnalyse

class PlanAnalyseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PlanAnalyse
        load_instance = True
        include_fk = True

class EchantillonSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Echantillon
        load_instance = True
        include_fk = True

class ResultatAnalyseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ResultatAnalyse
        load_instance = True
        include_fk = True
