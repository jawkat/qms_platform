from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.hse import (
    Incident, UniteTravail, DangerSst, EvaluationRisqueSst,
    CauseIncident, EPI, Inspection, InspectionItem, PermisTravail
)

class IncidentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Incident
        load_instance = True
        include_fk = True
    
    statut_label = fields.String(dump_only=True)

class UniteTravailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UniteTravail
        load_instance = True
        include_fk = True

class DangerSstSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = DangerSst
        load_instance = True
        include_fk = True

class EvaluationRisqueSstSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EvaluationRisqueSst
        load_instance = True
        include_fk = True
    
    criticite = fields.Int(dump_only=True)
    niveau_risque = fields.String(dump_only=True)

class CauseIncidentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CauseIncident
        load_instance = True
        include_fk = True

    enfants = fields.Nested('self', many=True, dump_only=True)

class EPISchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EPI
        load_instance = True
        include_fk = True

class InspectionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Inspection
        load_instance = True
        include_fk = True

class InspectionItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InspectionItem
        load_instance = True
        include_fk = True

class PermisTravailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PermisTravail
        load_instance = True
        include_fk = True
