from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.environnement import AspectEnvironnemental, SuiviEnvironnemental

class AspectEnvironnementalSchema(AutoSchema):
    class Meta:
        model = AspectEnvironnemental
        load_instance = True
        include_fk = True

class SuiviEnvironnementalSchema(AutoSchema):
    class Meta:
        model = SuiviEnvironnemental
        load_instance = True
        include_fk = True
