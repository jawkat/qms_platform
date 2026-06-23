from flask import request, abort
from flask_login import current_user
from app.extensions import db
from app.services.base import BaseService


class BaseResource:
    """Pont HTTP → Service.

    Responsabilités :
    - Lire la requête HTTP (request.args, request.get_json)
    - Récupérer le tenant courant (current_user.entreprise_id)
    - Déléguer les opérations CRUD au service
    - Protéger les champs sensibles (id, entreprise_id, date_creation)
    - Retourner 404 si l'item n'existe pas

    NE CONTIENT PAS de logique métier.  Pour ajouter des règles,
    créer une sous-classe de BaseService et la référencer via
    ``service_class``.

    Usage ::

        class FormationResource(BaseResource):
            model = Formation
            schema = FormationSchema
            service_class = FormationService  # optionnel
    """

    model = None
    schema = None
    service_class = None
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})
    sort_field = 'date_creation'
    sort_dir = 'desc'
    search_fields = []
    filter_fields = {}
    tenant_field = 'entreprise_id'

    # ------------------------------------------------------------------
    # Service
    # ------------------------------------------------------------------

    @classmethod
    def _get_service(cls):
        if cls.service_class is not None:
            return cls.service_class
        if cls.model is not None:
            return type(f'{cls.__name__}AutoService', (BaseService,), {'model': cls.model})
        return BaseService

    @classmethod
    def _get_entreprise_id(cls):
        if not cls.tenant_field or not current_user.is_authenticated:
            return None
        return current_user.entreprise_id

    # ------------------------------------------------------------------
    # Query — surchargeable pour filtres customs (PrpResource, …)
    # ------------------------------------------------------------------

    @classmethod
    def _query(cls):
        """Requête de base — le tenant scoping est assuré par l'Event Listener global."""
        return cls.model.query

    @classmethod
    def _uses_custom_query(cls):
        """True si une sous-classe a surchargé _query()."""
        return '_query' in cls.__dict__

    # ------------------------------------------------------------------
    # list_resources
    # ------------------------------------------------------------------

    @classmethod
    def list_resources(cls):
        if cls._uses_custom_query():
            q = cls._query()
            for param, col in cls.filter_fields.items():
                val = request.args.get(param)
                if val:
                    q = q.filter(getattr(cls.model, col) == val)
            search = request.args.get('q', '').strip()
            if search and cls.search_fields:
                like = f'%{search}%'
                conds = [getattr(cls.model, f).ilike(like) for f in cls.search_fields]
                q = q.filter(db.or_(*conds))
            sort_attr = getattr(cls.model, cls.sort_field, None)
            if sort_attr is not None:
                order = getattr(sort_attr, cls.sort_dir, None)
                if order is not None:
                    q = q.order_by(order())
            return q.all()

        svc = cls._get_service()
        eid = cls._get_entreprise_id()
        filters = {p: request.args[p] for p in cls.filter_fields if p in request.args}
        search = request.args.get('q', '').strip()
        return svc.list(
            entreprise_id=eid,
            filters=filters,
            search=search,
            search_fields=cls.search_fields,
            sort_field=cls.sort_field,
            sort_dir=cls.sort_dir,
        )

    # ------------------------------------------------------------------
    # get_resource
    # ------------------------------------------------------------------

    @classmethod
    def get_resource(cls, item_id):
        if cls._uses_custom_query():
            item = cls._query().filter(cls.model.id == item_id).first()
        else:
            item = cls._get_service().get_by_id(item_id, cls._get_entreprise_id())
        if not item:
            abort(404)
        return item

    # ------------------------------------------------------------------
    # create_resource
    # ------------------------------------------------------------------

    @classmethod
    def create_resource(cls, data):
        if cls.tenant_field:
            setattr(data, cls.tenant_field, cls._get_entreprise_id())
        return cls._get_service().save(data)

    # ------------------------------------------------------------------
    # update_resource
    # ------------------------------------------------------------------

    @classmethod
    def update_resource(cls, item_id):
        item = cls.get_resource(item_id)
        for field, value in request.get_json().items():
            if field not in cls.protected_fields and hasattr(item, field):
                setattr(item, field, value)
        return cls._get_service().save(item)

    # ------------------------------------------------------------------
    # delete_resource
    # ------------------------------------------------------------------

    @classmethod
    def delete_resource(cls, item_id):
        item = cls.get_resource(item_id)
        cls._get_service().remove(item)
        return {'success': True}
