"""Auto-enregistrement CRUD — supprime la duplication d'endpoints."""

import re

from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource


def auto_register_crud(blueprint, model, schema, module=None, name=None,
                       permission_voir=None, permission_gerer=None,
                       resource_cls=None, url_prefix='/api',
                       flat=False):
    """Auto-enregistre les 4 endpoints CRUD (list, create, update, delete).

    Usage moderne (HACCP) ::

        auto_register_crud(blueprint=haccp_bp, model=ProcessusHaccp,
                           schema=ProcessusHaccpSchema, module='haccp')

    Usage legacy (module mono-modèle) ::

        auto_register_crud(..., flat=True)
        # utilise les endpoints /api/liste, /api/creer, …
        # identiques à :meth:`blueprint.api_liste`, `blueprint.api_creer`, …

    Remplace 40 lignes de boilerplate par une seule ligne.
    """
    if name is None:
        name = model.__name__.lower()
    ep = re.sub(r'[^a-zA-Z0-9_]', '_', name)  # endpoint = name sans tirets
    aep = f'api_{ep}'  # convention templates: api_{name}

    voir = permission_voir or (f'{module}.voir' if module else None)
    gerer = permission_gerer or (f'{module}.gerer' if module else None)

    if resource_cls is None:
        resource_cls = type(
            f'{model.__name__}Resource',
            (BaseResource,),
            {'model': model, 'schema': schema},
        )

    kw = {}
    if module:
        kw['module'] = module

    if flat:
        # Mode legacy : URLs plates /api/liste, /api/creer, …
        @blueprint.get(f'{url_prefix}/liste', endpoint='api_liste')
        @blueprint.response(200, schema(many=True))
        @access_required(permission=voir, **kw)
        def _list():
            return resource_cls.list_resources()
        _list.__name__ = 'api_liste'

        @blueprint.post(f'{url_prefix}/creer', endpoint='api_creer')
        @blueprint.arguments(schema)
        @blueprint.response(201, schema)
        @access_required(permission=gerer, **kw)
        def _create(data):
            return resource_cls.create_resource(data)
        _create.__name__ = 'api_creer'

        @blueprint.post(f'{url_prefix}/<int:item_id>/modifier', endpoint='api_modifier')
        @blueprint.response(200, schema)
        @access_required(permission=gerer, **kw)
        def _update(item_id):
            return resource_cls.update_resource(item_id)
        _update.__name__ = 'api_modifier'

        @blueprint.post(f'{url_prefix}/<int:item_id>/supprimer', endpoint='api_supprimer')
        @access_required(permission=gerer, **kw)
        def _delete(item_id):
            return resource_cls.delete_resource(item_id)
        _delete.__name__ = 'api_supprimer'
    else:
        # Mode standard : URLs nommées par modèle
        base_url = f'{url_prefix}/{name}'

        @blueprint.get(base_url, endpoint=f'{aep}')
        @blueprint.response(200, schema(many=True))
        @access_required(permission=voir, **kw)
        def _list():
            return resource_cls.list_resources()
        _list.__name__ = f'{aep}'

        @blueprint.post(f'{base_url}/create', endpoint=f'{aep}_create')
        @blueprint.arguments(schema)
        @blueprint.response(201, schema)
        @access_required(permission=gerer, **kw)
        def _create(data):
            return resource_cls.create_resource(data)
        _create.__name__ = f'{aep}_create'

        @blueprint.post(f'{base_url}/<int:item_id>/update', endpoint=f'{aep}_update')
        @blueprint.response(200, schema)
        @access_required(permission=gerer, **kw)
        def _update(item_id):
            return resource_cls.update_resource(item_id)
        _update.__name__ = f'{aep}_update'

        @blueprint.post(f'{base_url}/<int:item_id>/delete', endpoint=f'{aep}_delete')
        @access_required(permission=gerer, **kw)
        def _delete(item_id):
            return resource_cls.delete_resource(item_id)
        _delete.__name__ = f'{aep}_delete'

    return resource_cls
