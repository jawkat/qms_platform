from app.services.base import BaseService
from app.models import Audit


class AuditService(BaseService):
    """Service Audit — pas de logique spécifique pour l'instant.

    Le domaine est injecté par AuditResource depuis la session Flask
    (préoccupation HTTP, pas métier).
    """
    model = Audit
