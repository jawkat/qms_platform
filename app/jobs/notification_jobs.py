from app import db
from app.models import Notification
from app.utils.notifications import create_notification


def send_bulk_notification(type_, message, user_ids=None, entreprise_id=None):
    if user_ids:
        for uid in user_ids:
            create_notification(type=type_, message=message, utilisateur_id=uid)
    elif entreprise_id:
        from app.models import Utilisateur
        users = Utilisateur.query.filter_by(entreprise_id=entreprise_id, actif=True).all()
        for u in users:
            create_notification(type=type_, message=message, utilisateur_id=u.id)
    db.session.commit()


def send_action_notifications(action, entreprise_id):
    from app.models import Utilisateur
    users = Utilisateur.query.filter_by(entreprise_id=entreprise_id, actif=True).all()
    for u in users:
        create_notification(
            type='action',
            message=f'Nouvelle action corrective: {action.description[:100]}',
            utilisateur_id=u.id,
        )
    db.session.commit()
