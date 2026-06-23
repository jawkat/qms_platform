from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.schemas.base import AutoSchema
from app.models.audit import Audit, AuditObservation, ChecklistModele as Checklist, ChecklistItem

class ChecklistSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Checklist
        load_instance = True
        include_fk = True

class ChecklistItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ChecklistItem
        load_instance = True
        include_fk = True

class AuditSchema(AutoSchema):
    class Meta:
        model = Audit
        load_instance = True
        include_fk = True
    
    statut_label = fields.String(dump_only=True)

class AuditObservationSchema(AutoSchema):
    class Meta:
        model = AuditObservation
        load_instance = True
        include_fk = True
