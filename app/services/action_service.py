from datetime import datetime, timedelta
from app.extensions import db
from app.models import ActionCorrective
from .base import BaseService

class ActionService(BaseService):
    """
    Service pour la gestion des actions correctives.
    Hérite de BaseService (get_by_id, create, update, delete).
    """
    model = ActionCorrective

    @classmethod
    def get_all_by_tenant(cls, entreprise_id, domaine=None, statut=None, priorite=None, source=None, search=None):
        q = cls.model.query.filter_by(entreprise_id=entreprise_id)
        if domaine:
            q = q.filter_by(domaine=domaine)
        if statut:
            q = q.filter(cls.model.statut == statut)
        if priorite:
            q = q.filter(cls.model.priorite == priorite)
        if source:
            q = q.filter(cls.model.source_type == source)
        if search:
            q = q.filter(cls.model.description.ilike(f'%{search}%'))
        return q.order_by(cls.model.date_creation.desc()).all()

    @classmethod
    def generate_next_occurrence(cls, action):
        """Génère la prochaine occurrence d'une action périodique"""
        if not action.est_recurrente or not action.frequence:
            return None
            
        base_date = action.date_echeance or datetime.utcnow().date()
        
        # Calcul de la nouvelle date selon la fréquence
        if action.frequence == 'hebdomadaire':
            new_date = base_date + timedelta(weeks=1)
        elif action.frequence == 'mensuel':
            new_date = cls._add_months(base_date, 1)
        elif action.frequence == 'trimestriel':
            new_date = cls._add_months(base_date, 3)
        elif action.frequence == 'annuel':
            new_date = cls._add_months(base_date, 12)
        else:
            return None
            
        new_action = cls.model(
            entreprise_id=action.entreprise_id,
            domaine=action.domaine,
            source_type=action.source_type,
            source_id=action.source_id,
            description=action.description,
            type_action=action.type_action,
            priorite=action.priorite,
            responsable_id=action.responsable_id,
            date_echeance=new_date,
            statut='A_FAIRE',
            est_recurrente=True,
            frequence=action.frequence,
            parent_action_id=action.id
        )
        
        db.session.add(new_action)
        db.session.commit()
        return new_action

    @staticmethod
    def _add_months(source_date, months):
        import calendar
        month = (source_date.month - 1 + months) % 12 + 1
        year = source_date.year + (source_date.month - 1 + months) // 12
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return source_date.replace(year=year, month=month, day=day)

    @classmethod
    def send_action_reminders(cls):
        """Envoie des rappels pour les actions arrivant à échéance"""
        from app.utils.notifications import send_action_reminder_email
        
        today = datetime.utcnow().date()
        reminder_dates = [
            today + timedelta(days=7),
            today + timedelta(days=3),
            today,
            today - timedelta(days=1) # En retard
        ]
        
        actions = cls.model.query.filter(
            cls.model.statut == 'A_FAIRE',
            cls.model.date_echeance.in_(reminder_dates)
        ).all()
        
        count = 0
        for action in actions:
            if action.responsable and action.responsable.email:
                if send_action_reminder_email(action):
                    count += 1
        return count
