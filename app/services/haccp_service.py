from app.services.base import BaseService
from app.models.haccp import Prp


class PrpService(BaseService):
    """Service PRP générique — type_prp='generic'."""
    model = Prp

    @classmethod
    def _base_query(cls, entreprise_id=None):
        return super()._base_query(entreprise_id).filter_by(type_prp='generic')

    @classmethod
    def save(cls, instance):
        instance.type_prp = 'generic'
        return super().save(instance)


class OprpService(BaseService):
    """Service PRP opérationnel — type_prp='operational'."""
    model = Prp

    @classmethod
    def _base_query(cls, entreprise_id=None):
        return super()._base_query(entreprise_id).filter_by(type_prp='operational')

    @classmethod
    def save(cls, instance):
        instance.type_prp = 'operational'
        return super().save(instance)
