from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models.haccp import (
    ProcessusHaccp, ProduitHaccp, MatierePremiere, AnalyseDanger,
    Ccp, EnregistrementCcp, Prp, EnregistrementOprp,
    TracabiliteLot, RappelProduit
)


class _OptionalEntrepriseMixin:
    entreprise_id = fields.Integer(required=False, load_default=None)


class ProcessusHaccpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = ProcessusHaccp
        load_instance = True
        include_fk = True


class ProduitHaccpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = ProduitHaccp
        load_instance = True
        include_fk = True


class MatierePremiereSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = MatierePremiere
        load_instance = True
        include_fk = True


class AnalyseDangerSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = AnalyseDanger
        load_instance = True
        include_fk = True
    
    ipr = fields.Int(dump_only=True)
    etape = fields.Function(lambda obj: obj.processus.etape if obj.processus else '', dump_only=True)


class CcpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Ccp
        load_instance = True
        include_fk = True


class EnregistrementCcpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = EnregistrementCcp
        load_instance = True
        include_fk = True


class PrpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = Prp
        load_instance = True
        include_fk = True
    
    etape = fields.Function(lambda obj: obj.processus.etape if obj.processus else '', dump_only=True)
    danger_libelle = fields.Function(lambda obj: obj.danger.danger if obj.danger else '', dump_only=True)


class EnregistrementOprpSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = EnregistrementOprp
        load_instance = True
        include_fk = True


class TracabiliteLotSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = TracabiliteLot
        load_instance = True
        include_fk = True


class RappelProduitSchema(_OptionalEntrepriseMixin, SQLAlchemyAutoSchema):
    class Meta:
        model = RappelProduit
        load_instance = True
        include_fk = True
