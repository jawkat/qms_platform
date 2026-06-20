from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.entreprise import Entreprise, HistoriquePaiement

class EntrepriseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Entreprise
        load_instance = True
        include_fk = True

class HistoriquePaiementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = HistoriquePaiement
        load_instance = True
        include_fk = True

class QuotaSchema(SQLAlchemyAutoSchema):
    used_users = fields.Int()
    max_users = fields.Int()
    used_actions = fields.Int()
    max_actions = fields.Int()
    used_documents = fields.Int()
    max_documents = fields.Int()
    used_storage_mb = fields.Float()
    max_storage_mb = fields.Float()
