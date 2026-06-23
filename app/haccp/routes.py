from flask import render_template
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.haccp import blueprint
from app.models import (
    ProcessusHaccp, ProduitHaccp, AnalyseDanger, Ccp,
    EnregistrementCcp, Prp, EnregistrementOprp,
    TracabiliteLot, RappelProduit,
)
from app.models.nonconformite import NonConformite
from app.schemas.haccp import (
    ProcessusHaccpSchema, ProduitHaccpSchema, AnalyseDangerSchema,
    CcpSchema, EnregistrementCcpSchema, PrpSchema, EnregistrementOprpSchema,
    TracabiliteLotSchema, RappelProduitSchema
)


# =============================================================================
# Resource definitions
# =============================================================================

class ProcessusHaccpResource(BaseResource):
    model = ProcessusHaccp
    schema = ProcessusHaccpSchema


class ProduitHaccpResource(BaseResource):
    model = ProduitHaccp
    schema = ProduitHaccpSchema


class AnalyseDangerResource(BaseResource):
    model = AnalyseDanger
    schema = AnalyseDangerSchema


class CcpResource(BaseResource):
    model = Ccp
    schema = CcpSchema


class EnregistrementCcpResource(BaseResource):
    model = EnregistrementCcp
    schema = EnregistrementCcpSchema
    sort_field = 'date_controle'


class EnregistrementOprpResource(BaseResource):
    model = EnregistrementOprp
    schema = EnregistrementOprpSchema
    sort_field = 'date_controle'


class TracabiliteLotResource(BaseResource):
    model = TracabiliteLot
    schema = TracabiliteLotSchema


class RappelProduitResource(BaseResource):
    model = RappelProduit
    schema = RappelProduitSchema


class PrpResource(BaseResource):
    model = Prp
    schema = PrpSchema

    @classmethod
    def _query(cls):
        return super()._query().filter_by(type_prp='generic')

    @classmethod
    def create_resource(cls, data):
        data.type_prp = 'generic'
        return super().create_resource(data)


class OprpResource(BaseResource):
    model = Prp
    schema = PrpSchema

    @classmethod
    def _query(cls):
        return super()._query().filter_by(type_prp='operational')

    @classmethod
    def create_resource(cls, data):
        data.type_prp = 'operational'
        return super().create_resource(data)


# =============================================================================
# Pages HTML
# =============================================================================

PAGES = [
    ('/', 'tableau_de_bord', 'haccp.voir'),
    ('/processus', 'processus', 'haccp.voir'),
    ('/produits', 'produits', 'haccp.voir'),
    ('/dangers', 'dangers', 'haccp.voir'),
    ('/ccp', 'ccp', 'haccp.voir'),
    ('/enregistrements', 'enregistrements', 'haccp.voir'),
    ('/prp', 'prp', 'haccp.voir'),
    ('/oprp', 'oprp', 'haccp.voir'),
    ('/enregistrements-oprp', 'enregistrements_oprp', 'haccp.voir'),
    ('/tracabilite', 'tracabilite', 'haccp.voir'),
    ('/rappels', 'rappels', 'haccp.voir'),
]


def _make_page(route, template_name, view_func):
    """Create a simple page endpoint."""
    return blueprint.route(route, endpoint=template_name)(view_func)


for route_url, template_name, _ in PAGES:
    def _build_page(tpl=template_name):
        return render_template(f'haccp/{tpl}.html')

    _make_page(route_url, template_name,
               access_required(module='haccp', permission='haccp.voir')(_build_page))


# =============================================================================
# API — Statistiques
# =============================================================================

@blueprint.get('/api/stats')
@access_required(module='haccp', permission='haccp.voir')
def api_stats():
    """Statistiques HACCP"""
    return {
        'processus': ProcessusHaccp.query.count(),
        'produits': ProduitHaccp.query.count(),
        'ccp': Ccp.query.count(),
        'dangers': AnalyseDanger.query.count(),
        'nonconformites': NonConformite.query.filter_by(domaine='haccp').count(),
        'enregistrements': EnregistrementCcp.query.count(),
        'prp': Prp.query.filter_by(type_prp='generic').count(),
        'oprp': Prp.query.filter_by(type_prp='operational').count(),
        'enregistrements_oprp': EnregistrementOprp.query.count(),
        'tracabilite': TracabiliteLot.query.count(),
        'rappels': RappelProduit.query.count(),
    }


# =============================================================================
# API — Analyse des dangers
# =============================================================================

@blueprint.get('/api/dangers')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, AnalyseDangerSchema(many=True))
def api_dangers():
    return AnalyseDangerResource.list_resources()


@blueprint.post('/api/dangers/create')
@access_required(module='haccp', permission='haccp.gerer_dangers')
@blueprint.arguments(AnalyseDangerSchema)
@blueprint.response(201, AnalyseDangerSchema)
def api_dangers_create(data):
    return AnalyseDangerResource.create_resource(data)


@blueprint.post('/api/dangers/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_dangers')
@blueprint.response(200, AnalyseDangerSchema)
def api_dangers_update(item_id):
    return AnalyseDangerResource.update_resource(item_id)


@blueprint.post('/api/dangers/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_dangers')
def api_dangers_delete(item_id):
    return AnalyseDangerResource.delete_resource(item_id)


# =============================================================================
# API — Processus HACCP
# =============================================================================

@blueprint.get('/api/processus')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, ProcessusHaccpSchema(many=True))
def api_processus():
    return ProcessusHaccpResource.list_resources()


@blueprint.post('/api/processus/create')
@access_required(module='haccp', permission='haccp.gerer_processus')
@blueprint.arguments(ProcessusHaccpSchema)
@blueprint.response(201, ProcessusHaccpSchema)
def api_processus_create(data):
    return ProcessusHaccpResource.create_resource(data)


@blueprint.post('/api/processus/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_processus')
@blueprint.response(200, ProcessusHaccpSchema)
def api_processus_update(item_id):
    return ProcessusHaccpResource.update_resource(item_id)


@blueprint.post('/api/processus/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_processus')
def api_processus_delete(item_id):
    return ProcessusHaccpResource.delete_resource(item_id)


# =============================================================================
# API — Produits
# =============================================================================

@blueprint.get('/api/produits')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, ProduitHaccpSchema(many=True))
def api_produits():
    return ProduitHaccpResource.list_resources()


@blueprint.post('/api/produits/create')
@access_required(module='haccp', permission='haccp.gerer_produits')
@blueprint.arguments(ProduitHaccpSchema)
@blueprint.response(201, ProduitHaccpSchema)
def api_produits_create(data):
    return ProduitHaccpResource.create_resource(data)


@blueprint.post('/api/produits/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_produits')
@blueprint.response(200, ProduitHaccpSchema)
def api_produits_update(item_id):
    return ProduitHaccpResource.update_resource(item_id)


@blueprint.post('/api/produits/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_produits')
def api_produits_delete(item_id):
    return ProduitHaccpResource.delete_resource(item_id)


# =============================================================================
# API — CCP
# =============================================================================

@blueprint.get('/api/ccp')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, CcpSchema(many=True))
def api_ccp():
    return CcpResource.list_resources()


@blueprint.post('/api/ccp/create')
@access_required(module='haccp', permission='haccp.gerer_ccp')
@blueprint.arguments(CcpSchema)
@blueprint.response(201, CcpSchema)
def api_ccp_create(data):
    return CcpResource.create_resource(data)


@blueprint.post('/api/ccp/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_ccp')
@blueprint.response(200, CcpSchema)
def api_ccp_update(item_id):
    return CcpResource.update_resource(item_id)


@blueprint.post('/api/ccp/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_ccp')
def api_ccp_delete(item_id):
    return CcpResource.delete_resource(item_id)


# =============================================================================
# API — Enregistrements CCP
# =============================================================================

@blueprint.get('/api/enregistrements')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, EnregistrementCcpSchema(many=True))
def api_enregistrements():
    return EnregistrementCcpResource.list_resources()


@blueprint.post('/api/enregistrements/create')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementCcpSchema)
@blueprint.response(201, EnregistrementCcpSchema)
def api_enregistrements_create(data):
    return EnregistrementCcpResource.create_resource(data)


@blueprint.post('/api/enregistrements/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
@blueprint.response(200, EnregistrementCcpSchema)
def api_enregistrements_update(item_id):
    return EnregistrementCcpResource.update_resource(item_id)


@blueprint.post('/api/enregistrements/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
def api_enregistrements_delete(item_id):
    return EnregistrementCcpResource.delete_resource(item_id)


# =============================================================================
# API — PRP
# =============================================================================

@blueprint.get('/api/prp')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, PrpSchema(many=True))
def api_prp():
    return PrpResource.list_resources()


@blueprint.post('/api/prp/create')
@access_required(module='haccp', permission='haccp.gerer_prp')
@blueprint.arguments(PrpSchema)
@blueprint.response(201, PrpSchema)
def api_prp_create(data):
    return PrpResource.create_resource(data)


@blueprint.post('/api/prp/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_prp')
@blueprint.response(200, PrpSchema)
def api_prp_update(item_id):
    return PrpResource.update_resource(item_id)


@blueprint.post('/api/prp/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_prp')
def api_prp_delete(item_id):
    return PrpResource.delete_resource(item_id)


# =============================================================================
# API — OPRP
# =============================================================================

@blueprint.get('/api/oprp')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, PrpSchema(many=True))
def api_oprp():
    return OprpResource.list_resources()


@blueprint.post('/api/oprp/create')
@access_required(module='haccp', permission='haccp.gerer_prp')
@blueprint.arguments(PrpSchema)
@blueprint.response(201, PrpSchema)
def api_oprp_create(data):
    return OprpResource.create_resource(data)


@blueprint.post('/api/oprp/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_prp')
@blueprint.response(200, PrpSchema)
def api_oprp_update(item_id):
    return OprpResource.update_resource(item_id)


@blueprint.post('/api/oprp/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_prp')
def api_oprp_delete(item_id):
    return OprpResource.delete_resource(item_id)


# =============================================================================
# API — Enregistrements OPRP
# =============================================================================

@blueprint.get('/api/enregistrements-oprp')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, EnregistrementOprpSchema(many=True))
def api_enregistrements_oprp():
    return EnregistrementOprpResource.list_resources()


@blueprint.post('/api/enregistrements-oprp/create')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementOprpSchema)
@blueprint.response(201, EnregistrementOprpSchema)
def api_enregistrements_oprp_create(data):
    return EnregistrementOprpResource.create_resource(data)


@blueprint.post('/api/enregistrements-oprp/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
@blueprint.response(200, EnregistrementOprpSchema)
def api_enregistrements_oprp_update(item_id):
    return EnregistrementOprpResource.update_resource(item_id)


@blueprint.post('/api/enregistrements-oprp/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_enregistrements')
def api_enregistrements_oprp_delete(item_id):
    return EnregistrementOprpResource.delete_resource(item_id)


# =============================================================================
# API — Traçabilité
# =============================================================================

@blueprint.get('/api/tracabilite')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, TracabiliteLotSchema(many=True))
def api_tracabilite():
    return TracabiliteLotResource.list_resources()


@blueprint.post('/api/tracabilite/create')
@access_required(module='haccp', permission='haccp.gerer_tracabilite')
@blueprint.arguments(TracabiliteLotSchema)
@blueprint.response(201, TracabiliteLotSchema)
def api_tracabilite_create(data):
    return TracabiliteLotResource.create_resource(data)


@blueprint.post('/api/tracabilite/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_tracabilite')
@blueprint.response(200, TracabiliteLotSchema)
def api_tracabilite_update(item_id):
    return TracabiliteLotResource.update_resource(item_id)


@blueprint.post('/api/tracabilite/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_tracabilite')
def api_tracabilite_delete(item_id):
    return TracabiliteLotResource.delete_resource(item_id)


# =============================================================================
# API — Rappels
# =============================================================================

@blueprint.get('/api/rappels')
@access_required(module='haccp', permission='haccp.voir')
@blueprint.response(200, RappelProduitSchema(many=True))
def api_rappels():
    return RappelProduitResource.list_resources()


@blueprint.post('/api/rappels/create')
@access_required(module='haccp', permission='haccp.gerer_rappels')
@blueprint.arguments(RappelProduitSchema)
@blueprint.response(201, RappelProduitSchema)
def api_rappels_create(data):
    return RappelProduitResource.create_resource(data)


@blueprint.post('/api/rappels/<int:item_id>/update')
@access_required(module='haccp', permission='haccp.gerer_rappels')
@blueprint.response(200, RappelProduitSchema)
def api_rappels_update(item_id):
    return RappelProduitResource.update_resource(item_id)


@blueprint.post('/api/rappels/<int:item_id>/delete')
@access_required(module='haccp', permission='haccp.gerer_rappels')
def api_rappels_delete(item_id):
    return RappelProduitResource.delete_resource(item_id)
