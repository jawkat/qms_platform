from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.nonconformite import NonConformite

class NonConformiteSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NonConformite
        load_instance = True
        include_fk = True

    responsable_name = fields.Function(
        lambda obj: f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else "",
        dump_only=True
    )
    validee_par_name = fields.Function(
        lambda obj: f"{obj.validee_par.prenom} {obj.validee_par.nom}" if obj.validee_par else "",
        dump_only=True
    )

class NonConformiteCreateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NonConformite
        load_instance = True
        include_fk = True
        exclude = ('id', 'date_creation', 'date_modification', 'date_validation_cloture', 'validee_par_id')

class NonConformiteUpdateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = NonConformite
        load_instance = True
        include_fk = True
        partial = True
        exclude = ('id', 'entreprise_id', 'date_creation', 'date_modification')
