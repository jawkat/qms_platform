from flask import request, abort
from flask_login import current_user
from app.extensions import db


class BaseResource:
    """Generic CRUD for any SQLAlchemy model with tenant scoping & field protection.

    Usage in a route file::

        class FormationResource(BaseResource):
            model = Formation
            schema = FormationSchema
            search_fields = ['titre', 'formateur']
            filter_fields = {'statut': 'statut', 'domaine': 'domaine'}

        @blueprint.get('/api/liste')
        @access_required(permission='formations.voir')
        @blueprint.response(200, FormationSchema(many=True))
        def api_liste():
            return FormationResource.list_resources()
    """

    model = None
    schema = None
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})
    sort_field = 'date_creation'
    sort_dir = 'desc'
    search_fields = []
    filter_fields = {}
    tenant_field = 'entreprise_id'

    @classmethod
    def _query(cls):
        """Base query scoped to current tenant."""
        q = cls.model.query
        if cls.tenant_field and current_user.is_authenticated and current_user.entreprise_id:
            q = q.filter(getattr(cls.model, cls.tenant_field) == current_user.entreprise_id)
        return q

    @classmethod
    def list_resources(cls):
        """GET /api/liste — filtre, cherche, trie et retourne tous les items."""
        q = cls._query()

        for param, col in cls.filter_fields.items():
            val = request.args.get(param)
            if val:
                q = q.filter(getattr(cls.model, col) == val)

        search = request.args.get('q', '').strip()
        if search and cls.search_fields:
            like = f'%{search}%'
            filters = [getattr(cls.model, f).ilike(like) for f in cls.search_fields]
            q = q.filter(db.or_(*filters))

        sort_attr = getattr(cls.model, cls.sort_field, None)
        if sort_attr is not None:
            order = getattr(sort_attr, cls.sort_dir, None)
            if order is not None:
                q = q.order_by(order())

        return q.all()

    @classmethod
    def get_resource(cls, item_id):
        """GET /api/<id> — retourne un item ou 404."""
        item = cls._query().filter(cls.model.id == item_id).first()
        if not item:
            abort(404)
        return item

    @classmethod
    def create_resource(cls, data):
        """POST /api/creer — assigne l'entreprise, ajoute et commit."""
        if cls.tenant_field and hasattr(data, cls.tenant_field):
            setattr(data, cls.tenant_field, current_user.entreprise_id)
        db.session.add(data)
        db.session.commit()
        return data

    @classmethod
    def update_resource(cls, item_id):
        """POST /api/<id>/modifier — met à jour depuis request.get_json()."""
        item = cls.get_resource(item_id)
        for field, value in request.get_json().items():
            if field not in cls.protected_fields and hasattr(item, field):
                setattr(item, field, value)
        db.session.commit()
        return item

    @classmethod
    def delete_resource(cls, item_id):
        """POST /api/<id>/supprimer — supprime et commit."""
        item = cls.get_resource(item_id)
        db.session.delete(item)
        db.session.commit()
        return {'success': True}
