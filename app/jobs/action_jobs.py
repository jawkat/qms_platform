from datetime import datetime, timedelta
from app import db
from app.models import ActionCorrective
from app.utils.notifications import create_notification


def generate_recurring_actions():
    actions = ActionCorrective.query.filter(
        ActionCorrective.est_recurrente == True,
        ActionCorrective.statut.in_(['TERMINE', 'CLOTURE']),
    ).all()
    count = 0
    for action in actions:
        next_occurrence = _compute_next_occurrence(action)
        if next_occurrence:
            new_action = ActionCorrective(
                entreprise_id=action.entreprise_id,
                domaine=action.domaine,
                description=action.description,
                type_action=action.type_action,
                priorite=action.priorite,
                responsable_id=action.responsable_id,
                date_echeance=next_occurrence,
                statut='A_FAIRE',
                source_type='recurrence',
                source_id=action.id,
                est_recurrente=True,
                frequence=action.frequence,
            )
            db.session.add(new_action)
            create_notification(
                type='action',
                message=f"Nouvelle occurrence d'action récurrente: {action.description[:100]}",
                utilisateur_id=action.responsable_id or action.cree_par_id,
            )
            count += 1
    db.session.commit()
    return count


def _compute_next_occurrence(action):
    base_date = action.date_echeance or datetime.utcnow().date()
    if action.frequence == 'hebdomadaire':
        return base_date + timedelta(weeks=1)
    elif action.frequence == 'mensuel':
        month = base_date.month % 12 + 1
        year = base_date.year + (base_date.month // 12)
        try:
            return base_date.replace(year=year, month=month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return base_date.replace(year=year, month=month, day=last_day)
    elif action.frequence == 'trimestriel':
        new_month = base_date.month + 3
        new_year = base_date.year
        if new_month > 12:
            new_month -= 12
            new_year += 1
        try:
            return base_date.replace(year=new_year, month=new_month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(new_year, new_month)[1]
            return base_date.replace(year=new_year, month=new_month, day=last_day)
    elif action.frequence == 'annuel':
        try:
            return base_date.replace(year=base_date.year + 1)
        except ValueError:
            return base_date + timedelta(days=365)
    return None
