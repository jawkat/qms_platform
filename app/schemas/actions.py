from marshmallow import Schema, fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import ActionCorrective, ProofReference

class ActionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ActionCorrective
        load_instance = True
        include_fk = True

    statut_label = fields.String(dump_only=True)
    responsable_name = fields.Function(lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else None, dump_only=True)

class ActionCreateSchema(Schema):
    titre = fields.String(required=True)
    description = fields.String(required=True)
    type_action = fields.String(required=True)
    priorite = fields.String(dump_default="moyenne")
    date_echeance = fields.Date()
    responsable_id = fields.Int()
    source_type = fields.String()
    source_id = fields.Int()

class ActionReferenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProofReference
        load_instance = True
        include_fk = True
    
    nom_fichier = fields.Function(lambda obj: obj.proof_master.nom_fichier if obj.proof_master else "?", dump_only=True)
