from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.ged import Dossier, TypeDocument
from app.models.proofs import ProofMaster

class DossierSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Dossier
        load_instance = True
        include_fk = True
    
    doc_count = fields.Integer(dump_only=True)
    children = fields.List(fields.Nested(lambda: DossierSchema()), dump_only=True)

class TypeDocumentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = TypeDocument
        load_instance = True
        include_fk = True

class ProofMasterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ProofMaster
        load_instance = True
        include_fk = True
    
    uploader_name = fields.Function(
        lambda obj: f"{obj.uploader.prenom} {obj.uploader.nom}" if obj.uploader else "",
        dump_only=True
    )
    dossier_nom = fields.Function(
        lambda obj: obj.dossier.nom if obj.dossier else "",
        dump_only=True
    )
    type_nom = fields.Function(
        lambda obj: obj.type_doc.nom if obj.type_doc else "",
        dump_only=True
    )
    approbateur_name = fields.Function(
        lambda obj: f"{obj.approbateur.prenom} {obj.approbateur.nom}" if obj.approbateur else "",
        dump_only=True
    )
