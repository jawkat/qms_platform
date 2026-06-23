from app.services.base import BaseService
from app.models.partages import Fournisseur


class FournisseurService(BaseService):
    """Service Fournisseur — recalcule le score après chaque sauvegarde."""
    model = Fournisseur

    @classmethod
    def save(cls, instance):
        instance.calculer_score_global()
        return super().save(instance)
