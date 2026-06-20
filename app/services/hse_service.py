from app.services.base import BaseService
from app.models.hse import Incident, DangerSst, EvaluationRisqueSst
from app.extensions import db

class IncidentService(BaseService):
    model = Incident

    @classmethod
    def cloturer_incident(cls, incident_id, entreprise_id):
        from datetime import date
        return cls.update(incident_id, entreprise_id, statut='cloture', date_cloture=date.today())

class RisqueService(BaseService):
    model = EvaluationRisqueSst

    @classmethod
    def get_risques_critiques(cls, entreprise_id):
        # We need to filter based on property, but we can filter on raw columns for performance then sort
        risques = cls.get_all_by_tenant(entreprise_id)
        return sorted([r for r in risques if r.criticite >= 27], key=lambda x: x.criticite, reverse=True)
