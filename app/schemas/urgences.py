from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.urgences import PlanUrgence, ExerciceEvacuation, MainCourante

class PlanUrgenceSchema(AutoSchema):
    class Meta:
        model = PlanUrgence
        load_instance = True
        include_fk = True

class ExerciceEvacuationSchema(AutoSchema):
    class Meta:
        model = ExerciceEvacuation
        load_instance = True
        include_fk = True

class MainCouranteSchema(AutoSchema):
    class Meta:
        model = MainCourante
        load_instance = True
        include_fk = True
