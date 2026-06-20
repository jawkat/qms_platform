from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.environnement import AspectEnvironnemental, SuiviEnvironnemental

class AspectEnvironnementalSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AspectEnvironnemental
        load_instance = True
        include_fk = True

class SuiviEnvironnementalSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SuiviEnvironnemental
        load_instance = True
        include_fk = True
