from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.indicateurs import Indicateur, IndicateurValeur

class IndicateurSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Indicateur
        load_instance = True
        include_fk = True

class IndicateurValeurSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IndicateurValeur
        load_instance = True
        include_fk = True
