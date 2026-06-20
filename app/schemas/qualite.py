from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.qualite import ObjectifQualite, Risque, Equipement, EnregistrementEtalonnage, ControleQualite, RevueDirection

class ObjectifQualiteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ObjectifQualite
        load_instance = True
        include_fk = True
    
    progression = fields.Int(dump_only=True)

class RisqueSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Risque
        load_instance = True
        include_fk = True
    
    ipr = fields.Int(dump_only=True)
    niveau_risque = fields.Str(dump_only=True)
    responsable_name = fields.Function(
        lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else "",
        dump_only=True
    )

class EquipementSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Equipement
        load_instance = True
        include_fk = True

class EnregistrementEtalonnageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = EnregistrementEtalonnage
        load_instance = True
        include_fk = True

class ControleQualiteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ControleQualite
        load_instance = True
        include_fk = True

class RevueDirectionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RevueDirection
        load_instance = True
        include_fk = True
