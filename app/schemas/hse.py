from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.hse import (
    Incident, UniteTravail, DangerSst, EvaluationRisqueSst,
    CauseIncident, EPI, Inspection, InspectionItem, PermisTravail
)

class IncidentSchema(AutoSchema):
    class Meta:
        model = Incident
        load_instance = True
        include_fk = True
    
    statut_label = fields.String(dump_only=True)

class UniteTravailSchema(AutoSchema):
    class Meta:
        model = UniteTravail
        load_instance = True
        include_fk = True

class DangerSstSchema(AutoSchema):
    class Meta:
        model = DangerSst
        load_instance = True
        include_fk = True

class EvaluationRisqueSstSchema(AutoSchema):
    class Meta:
        model = EvaluationRisqueSst
        load_instance = True
        include_fk = True
    
    criticite = fields.Int(dump_only=True)
    niveau_risque = fields.String(dump_only=True)

class CauseIncidentSchema(AutoSchema):
    class Meta:
        model = CauseIncident
        load_instance = True
        include_fk = True

    enfants = fields.Nested('self', many=True, dump_only=True)

class EPISchema(AutoSchema):
    class Meta:
        model = EPI
        load_instance = True
        include_fk = True

class InspectionSchema(AutoSchema):
    class Meta:
        model = Inspection
        load_instance = True
        include_fk = True

class InspectionItemSchema(AutoSchema):
    class Meta:
        model = InspectionItem
        load_instance = True
        include_fk = True

class PermisTravailSchema(AutoSchema):
    class Meta:
        model = PermisTravail
        load_instance = True
        include_fk = True
