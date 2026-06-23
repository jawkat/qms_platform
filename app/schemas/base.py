from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema


class AutoSchema(SQLAlchemyAutoSchema):
    """Base schema that makes entreprise_id optional (set server-side)."""
    entreprise_id = fields.Integer(required=False, load_default=None)
