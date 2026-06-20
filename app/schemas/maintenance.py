from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.maintenance import EquipementMaintenance, InterventionMaintenance

class EquipementMaintenanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EquipementMaintenance
        load_instance = True
        include_fk = True

class InterventionMaintenanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InterventionMaintenance
        load_instance = True
        include_fk = True
