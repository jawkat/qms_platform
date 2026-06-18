from datetime import datetime, timedelta
from app import db
from app.models import ActionCorrective
from flask import current_app

class ActionService:
    @staticmethod
    def generate_next_occurrence(action):
        """Génère la prochaine occurrence d'une action périodique"""
        if not action.est_recurrente or not action.frequence:
            return None
            
        # Calculer la nouvelle date d'échéance
        base_date = action.date_echeance or datetime.utcnow().date()
        
        if action.frequence == 'hebdomadaire':
            new_date = base_date + timedelta(weeks=1)
        elif action.frequence == 'mensuel':
            # Utilisation de timedelta 30j pour simplifier ou calcul exact
            month = base_date.month % 12 + 1
            year = base_date.year + (base_date.month // 12)
            try:
                new_date = base_date.replace(year=year, month=month)
            except ValueError:
                # Si le jour n'existe pas (ex: 31 Jan -> 31 Fev), on prend le dernier jour du mois
                import calendar
                last_day = calendar.monthrange(year, month)[1]
                new_date = base_date.replace(year=year, month=month, day=last_day)
        elif action.frequence == 'trimestriel':
            month = (base_date.month + 2) % 12 + 1
            year = base_date.year + ((base_date.month + 2) // 12)
            try:
                # Correction pour le saut de 3 mois
                new_month = base_date.month + 3
                new_year = base_date.year
                if new_month > 12:
                    new_month -= 12
                    new_year += 1
                new_date = base_date.replace(year=new_year, month=new_month)
            except ValueError:
                import calendar
                new_month = base_date.month + 3
                new_year = base_date.year
                if new_month > 12:
                    new_month -= 12
                    new_year += 1
                last_day = calendar.monthrange(new_year, new_month)[1]
                new_date = base_date.replace(year=new_year, month=new_month, day=last_day)
        elif action.frequence == 'annuel':
            try:
                new_date = base_date.replace(year=base_date.year + 1)
            except ValueError:
                # Cas rare : 29 fevrier une année bissextile
                new_date = base_date.replace(year=base_date.year + 1, month=2, day=28)
        else:
            return None
            
        new_action = ActionCorrective(
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
    def process_all_periodic_actions():
        """Tâche de fond pour vérifier les récurrences et générer les nouvelles occurrences si nécessaire"""
        # On cherche les actions récurrentes réalisées qui n'ont pas encore d'occurrence suivante active
        # Dans notre logique actuelle, c'est fait au moment du "update", 
        # mais cette méthode peut servir de sécurité ou de déclencheur temporel
        pass

    @staticmethod
    def send_action_reminders():
        """Envoie des rappels pour les actions arrivant à échéance (7j, 3j, Jour J et Retard)"""
        from app.utils.notifications import send_action_reminder_email
        
        today = datetime.utcnow().date()
        
        # 1. Actions à échéance dans 7 jours, 3 jours, ou aujourd'hui
        reminder_dates = [
            today + timedelta(days=7),
            today + timedelta(days=3),
            today
        ]
        
        # 2. Actions en retard (optionnel : on peut limiter aux actions en retard depuis 1 jour pour ne pas spammer)
        overdue_date = today - timedelta(days=1)
        
        all_reminder_dates = reminder_dates + [overdue_date]
        
        actions = ActionCorrective.query.filter(
            ActionCorrective.statut == 'A_FAIRE',
            ActionCorrective.date_echeance.in_(all_reminder_dates)
        ).all()
        
        count = 0
        for action in actions:
            if action.responsable and action.responsable.email:
                if send_action_reminder_email(action):
                    count += 1
        return count
