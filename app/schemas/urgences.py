from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.urgences import PlanUrgence, ExerciceEvacuation, MainCourante

class PlanUrgenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PlanUrgence
        load_instance = True
        include_fk = True

class ExerciceEvacuationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ExerciceEvacuation
        load_instance = True
        include_fk = True

class MainCouranteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MainCourante
        load_instance = True
        include_fk = True
