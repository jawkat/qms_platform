from app.extensions import db

class BaseService:
    """
    Service de base pour encapsuler la logique métier générique.
    """
    model = None

    @classmethod
    def get_by_id(cls, item_id, entreprise_id=None):
        query = cls.model.query.filter_by(id=item_id)
        if entreprise_id:
            query = query.filter_by(entreprise_id=entreprise_id)
        return query.first()

    @classmethod
    def get_all_by_tenant(cls, entreprise_id):
        return cls.model.query.filter_by(entreprise_id=entreprise_id).all()

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
