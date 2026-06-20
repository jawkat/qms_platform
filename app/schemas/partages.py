from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.partages import Fournisseur, Formation, Reclamation

class FournisseurSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Fournisseur
        load_instance = True
        include_fk = True
    
    score_global = fields.Float(dump_only=True)

class FormationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Formation
        load_instance = True
        include_fk = True

class ReclamationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Reclamation
        load_instance = True
        include_fk = True
    
    responsable_name = fields.Function(
        lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else "",
        dump_only=True
    )
