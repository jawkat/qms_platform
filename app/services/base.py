from app.extensions import db
from app.utils.tenant_scope import current_entreprise_id


class BaseService:
    """Logique métier pure — aucune dépendance Flask.

    Responsabilités :
    - CRUD générique (get_by_id, list, create, update, delete)
    - Règles métier, calculs, validations avancées
    - Appels à des services externes (API, storage, email…)

    N'UTILISE PAS request, session, current_user, abort.
    Toutes les dépendances (entreprise_id, filters, …) sont passées
    explicitement en paramètre.
    """

    model = None

    # ------------------------------------------------------------------
    # Query builder — surchargeable pour filtres customs (PrpService, …)
    # ------------------------------------------------------------------

    @classmethod
    def _base_query(cls, entreprise_id=None):
        """Requête de base — le tenant scoping vient du ContextVar en priorité.

        À surcharger dans les sous-classes qui ont besoin d'un
        filtrage supplémentaire (ex : PrpService filtre par type_prp).
        """
        query = cls.model.query
        eid = current_entreprise_id.get() or entreprise_id
        if eid and hasattr(cls.model, 'entreprise_id'):
            query = query.filter_by(entreprise_id=eid)
        return query

    # ------------------------------------------------------------------
    # Lecture
    # ------------------------------------------------------------------

    @classmethod
    def get_by_id(cls, item_id, entreprise_id=None):
        return cls._base_query(entreprise_id).filter_by(id=item_id).first()

    @classmethod
    def get_all_by_tenant(cls, entreprise_id):
        return cls._base_query(entreprise_id).all()

    @classmethod
    def list(cls, entreprise_id=None, filters=None, search=None,
             search_fields=None, sort_field=None, sort_dir='desc'):
        """Liste filtrée, recherchée et triée — remplace un _query() manuel."""
        query = cls._base_query(entreprise_id)

        if filters:
            for field, value in filters.items():
                if value is not None and value != '':
                    query = query.filter(getattr(cls.model, field) == value)

        if search and search_fields:
            like = f'%{search}%'
            conds = [getattr(cls.model, f).ilike(like) for f in search_fields]
            query = query.filter(db.or_(*conds))

        if sort_field is not None:
            col = getattr(cls.model, sort_field, None)
            if col is not None:
                order = getattr(col, sort_dir, None)
                if order is not None:
                    query = query.order_by(order())

        return query.all()

    # ------------------------------------------------------------------
    # Écriture — API ``**kwargs`` (utilisée par ActionService, …)
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, **kwargs):
        instance = cls.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def update(cls, item_id, entreprise_id=None, **kwargs):
        instance = cls.get_by_id(item_id, entreprise_id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.commit()
        return instance

    @classmethod
    def delete(cls, item_id, entreprise_id=None):
        instance = cls.get_by_id(item_id, entreprise_id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
            return True
        return False

    # ------------------------------------------------------------------
    # Écriture — API ``instance`` (utilisée par BaseResource)
    # ------------------------------------------------------------------

    @classmethod
    def save(cls, instance):
        """Persiste une instance déjà construite (add + commit)."""
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def remove(cls, instance):
        """Supprime une instance déjà chargée (delete + commit)."""
        db.session.delete(instance)
        db.session.commit()
