from marshmallow import fields
from app.schemas.base import AutoSchema
from app.models.maintenance import EquipementMaintenance, InterventionMaintenance

class EquipementMaintenanceSchema(AutoSchema):
    class Meta:
        model = EquipementMaintenance
        load_instance = True
        include_fk = True

class InterventionMaintenanceSchema(AutoSchema):
    class Meta:
        model = InterventionMaintenance
        load_instance = True
        include_fk = True
