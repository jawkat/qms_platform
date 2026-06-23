from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.laboratoire import PlanAnalyse, Echantillon, ResultatAnalyse

class PlanAnalyseSchema(AutoSchema):
    class Meta:
        model = PlanAnalyse
        load_instance = True
        include_fk = True

class EchantillonSchema(AutoSchema):
    class Meta:
        model = Echantillon
        load_instance = True
        include_fk = True

class ResultatAnalyseSchema(AutoSchema):
    class Meta:
        model = ResultatAnalyse
        load_instance = True
        include_fk = True
