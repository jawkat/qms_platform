from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.connaissances import REX, FAQ

class REXSchema(AutoSchema):
    class Meta:
        model = REX
        load_instance = True
        include_fk = True

class FAQSchema(AutoSchema):
    class Meta:
        model = FAQ
        load_instance = True
        include_fk = True
