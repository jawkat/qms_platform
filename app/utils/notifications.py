from app import db
from app.models import Notification


def create_notification(user_id, message, type='info'):
    notif = Notification(
        utilisateur_id=user_id,
        message=message,
        type=type,
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def send_action_reminder_email(action):
    return False
