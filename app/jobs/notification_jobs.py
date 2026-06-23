from app import db
from app.models import Notification
from app.utils.notifications import create_notification


def send_bulk_notification(type_, message, user_ids=None, entreprise_id=None):
    if user_ids:
        for uid in user_ids:
            create_notification(uid, message, type=type_)
    elif entreprise_id:
        from app.models import Utilisateur
        users = Utilisateur.query.filter_by(entreprise_id=entreprise_id, actif=True).all()
        for u in users:
            create_notification(u.id, message, type=type_)
    db.session.commit()


def send_action_notifications(action, entreprise_id):
    from app.models import Utilisateur
    users = Utilisateur.query.filter_by(entreprise_id=entreprise_id, actif=True).all()
    for u in users:
        create_notification(
            u.id,
            f'Nouvelle action corrective: {action.description[:100]}',
            type='action',
        )
    db.session.commit()
