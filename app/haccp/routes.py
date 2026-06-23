from flask import render_template
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app.services.haccp_service import PrpService, OprpService
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
    TracabiliteLotSchema, RappelProduitSchema,
)


# =============================================================================
# Resources avec logique spécifique (déléguée aux services)
# =============================================================================

class PrpResource(BaseResource):
    model = Prp
    schema = PrpSchema
    service_class = PrpService


class OprpResource(BaseResource):
    model = Prp
    schema = PrpSchema
    service_class = OprpService


# =============================================================================
# Auto-enregistrement CRUD — 10 entités, 40 endpoints
# =============================================================================

auto_register_crud(blueprint, ProcessusHaccp, ProcessusHaccpSchema, module='haccp', name='processus',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_processus')
auto_register_crud(blueprint, ProduitHaccp, ProduitHaccpSchema, module='haccp', name='produits',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_produits')
auto_register_crud(blueprint, AnalyseDanger, AnalyseDangerSchema, module='haccp', name='dangers',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_dangers')
auto_register_crud(blueprint, Ccp, CcpSchema, module='haccp', name='ccp',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_ccp')
auto_register_crud(blueprint, EnregistrementCcp, EnregistrementCcpSchema, module='haccp', name='enregistrements',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_enregistrements')
auto_register_crud(blueprint, Prp, PrpSchema, module='haccp', name='prp',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_prp',
                   resource_cls=PrpResource)
auto_register_crud(blueprint, Prp, PrpSchema, module='haccp', name='oprp',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_prp',
                   resource_cls=OprpResource)
auto_register_crud(blueprint, EnregistrementOprp, EnregistrementOprpSchema, module='haccp', name='enregistrements-oprp',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_enregistrements')
auto_register_crud(blueprint, TracabiliteLot, TracabiliteLotSchema, module='haccp', name='tracabilite',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_tracabilite')
auto_register_crud(blueprint, RappelProduit, RappelProduitSchema, module='haccp', name='rappels',
                   permission_voir='haccp.voir', permission_gerer='haccp.gerer_rappels')


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
    return blueprint.route(route, endpoint=template_name)(view_func)


for route_url, template_name, _ in PAGES:
    def _build_page(tpl=template_name):
        return render_template(f'haccp/{tpl}.html')

    _make_page(route_url, template_name,
               access_required(module='haccp', permission='haccp.voir')(_build_page))


# =============================================================================
# API — Statistiques (logique métier, pas de CRUD)
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
