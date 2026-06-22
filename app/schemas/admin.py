from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.extensions import db
from app.models.entreprise import Entreprise, HistoriquePaiement

class EntrepriseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Entreprise
        load_instance = True
        include_fk = True
        sqla_session = db.session

class HistoriquePaiementSchema(SQLAlchemyAutoSchema):
    entreprise_id = fields.Integer(required=False)
    id = fields.Integer(dump_only=True)
    date_creation = fields.DateTime(dump_only=True)
    date_modification = fields.DateTime(dump_only=True)

    class Meta:
        model = HistoriquePaiement
        load_instance = True
        include_fk = True
        sqla_session = db.session

class QuotaSchema(SQLAlchemyAutoSchema):
    used_users = fields.Int()
    max_users = fields.Int()
    used_actions = fields.Int()
    max_actions = fields.Int()
    used_documents = fields.Int()
    max_documents = fields.Int()
    used_storage_mb = fields.Float()
    max_storage_mb = fields.Float()
