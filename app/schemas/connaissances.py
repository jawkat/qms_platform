from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.connaissances import REX, FAQ

class REXSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = REX
        load_instance = True
        include_fk = True

class FAQSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FAQ
        load_instance = True
        include_fk = True
