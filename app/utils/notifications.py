import logging
import time
from functools import wraps
from flask import render_template, url_for, current_app
from smtplib import SMTPException
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Notification
from datetime import datetime


logger = logging.getLogger(__name__)


def create_notification(user_id, message, type='info'):
    from flask import current_app
    notification = Notification(
        type=type,
        message=message,
        utilisateur_id=user_id,
        date_envoi=datetime.utcnow(),
        lu=False,
    )
    try:
        db.session.add(notification)
        db.session.commit()
        logger.info("Notification creee user_id=%s type=%s", user_id, type)
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Erreur SQL notification user_id=%s", user_id)


def notify_action(message_template, notification_type='info'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            if 'user_id' in kwargs:
                user_id = kwargs['user_id']
                message = message_template.format(user=user_id)
                try:
                    create_notification(user_id, message, notification_type)
                except Exception:
                    logger.exception("Erreur notification asynchrone user_id=%s", user_id)
            return result
        return decorated_function
    return decorator


def notify_users(users, message, type='info'):
    for user in users:
        user_id = user.id if hasattr(user, 'id') else user
        create_notification(user_id, message, type)


def send_account_created_email(recipient_email, recipient_name, role_name=None, login_link=None, activation_link=None):
    try:
        from app import mail
        from flask_mail import Message

        if not login_link:
            login_link = current_app.config.get('APP_LOGIN_URL', 'http://localhost:5005/')

        subject_base = current_app.config.get('MAIL_SUBJECT_NEW_ACCOUNT', 'Activez votre compte QMS')
        if role_name:
            subject = f"{subject_base} — {role_name}"
        else:
            subject = subject_base

        text_body = (
            f"Bonjour {recipient_name},\n\n"
            f"Votre compte QMS Platform est pret.\n"
        )
        if role_name:
            text_body += f"Role attribue : {role_name}\n"
        if activation_link:
            text_body += f"Activez votre compte ici : {activation_link}\n"
        text_body += (
            f"Une fois le mot de passe defini, connectez-vous ici: {login_link}\n\n"
            "Si vous n'avez pas demande la creation de ce compte, ignorez cet e-mail."
        )

        html_body = render_template(
            'emails/account_created.html',
            recipient_name=recipient_name,
            role_name=role_name,
            activation_link=activation_link,
            login_link=login_link,
            subject=subject,
        )

        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        msg = Message(subject=subject, recipients=[recipient_email], sender=sender)
        msg.body = text_body
        msg.html = html_body

        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info("Email creation compte simule pour %s", recipient_email)
            return True

        mail.send(msg)
        logger.info("Email creation compte envoye a %s", recipient_email)
        return True
    except (ImportError, RuntimeError):
        logger.exception("Erreur init mail creation compte %s", recipient_email)
        return False
    except (SMTPException, OSError, ValueError):
        logger.exception("Erreur envoi email creation compte %s", recipient_email)
        return False


def send_password_reset_email(user):
    try:
        from app import mail
        from flask_mail import Message

        token = user.get_reset_token()
        reset_url = url_for('users.reset_password_token', token=token, _external=True)

        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info("Email reset simule pour %s : %s", user.email, reset_url)
            return True

        subject = "Reinitialisation de votre mot de passe QMS"
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@qmsplatform.ma')

        text_body = (
            f"Bonjour {user.prenom},\n\n"
            f"Pour reinitialiser votre mot de passe, cliquez sur le lien ci-dessous :\n"
            f"{reset_url}\n\n"
            f"Ce lien est valide pendant 30 minutes.\n"
            f"Si vous n'avez pas demande une reinitialisation de mot de passe, "
            f"veuillez ignorer cet e-mail.\n\n"
            f"Cordialement,\nL'equipe QMS"
        )

        html_body = (
            f"<p>Bonjour {user.prenom},</p>"
            f"<p>Pour reinitialiser votre mot de passe, "
            f"<a href=\"{reset_url}\">cliquez ici</a>.</p>"
            f"<p><strong>Ce lien est valide pendant 30 minutes.</strong></p>"
            f"<p>Si vous n'avez pas demande une reinitialisation de mot de passe, "
            f"veuillez ignorer cet e-mail.</p>"
            f"<p>Cordialement,<br>L'equipe QMS</p>"
        )

        msg = Message(subject=subject, recipients=[user.email], sender=sender)
        msg.body = text_body
        msg.html = html_body

        mail.send(msg)
        logger.info("Email reset envoye a %s", user.email)
        return True
    except (ImportError, RuntimeError):
        logger.exception("Erreur init mail reset pour %s", user.email)
        return False
    except (SMTPException, OSError, ValueError):
        logger.exception("Erreur envoi email reset pour %s", user.email)
        return False


def send_action_reminder_email(action):
    try:
        from app import mail
        from flask_mail import Message

        user = action.responsable
        if not user or not user.email:
            return False

        subject = f"Rappel QMS : Action a echeance le {action.date_echeance.strftime('%d/%m/%Y')}"
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@qmsplatform.ma')

        today = datetime.utcnow().date()
        days_remaining = (action.date_echeance - today).days

        action_url = url_for('actions.liste_actions', _external=True)

        html_body = render_template(
            'emails/action_reminder.html',
            user=user,
            action=action,
            days_remaining=days_remaining,
            action_url=action_url,
            subject=subject,
        )

        text_body = (
            f"Bonjour {user.prenom},\n\n"
            f"Ceci est un rappel pour l'action suivante : {action.description}\n"
            f"Echeance : {action.date_echeance.strftime('%d/%m/%Y')} "
            f"({days_remaining} jours restants).\n\n"
            f"Lien : {action_url}\n\n"
            f"L'equipe QMS"
        )

        msg = Message(subject=subject, recipients=[user.email], sender=sender)
        msg.body = text_body
        msg.html = html_body

        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info("Email rappel simule pour %s (Action: %s)", user.email, action.id)
            return True

        mail.send(msg)
        logger.info("Email rappel envoye a %s pour l'action %s", user.email, action.id)
        return True
    except Exception:
        logger.exception("Erreur envoi email rappel action %s", action.id)
        return False


def send_incident_email(error_message, request_id, path, method, user_info='-'):
    try:
        from app import mail
        from flask_mail import Message

        recipient = current_app.config.get('MAIL_ADMIN_EMAIL', 'jwd.katten@gmail.com')
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@qmsplatform.ma')

        subject = f"INCIDENT QMS : {type(error_message).__name__ if not isinstance(error_message, str) else 'Exception'}"

        text_body = (
            f"Un incident critique a ete detecte sur la plateforme QMS.\n\n"
            f"Reference : {request_id}\n"
            f"Chemin : {method} {path}\n"
            f"Utilisateur : {user_info}\n"
            f"Erreur : {str(error_message)}\n\n"
            f"Veuillez consulter les logs du serveur pour plus de details."
        )

        html_body = (
            f"<h2 style='color: #dc3545;'>Incident Critique Detecte</h2>"
            f"<p><strong>Reference :</strong> <code>{request_id}</code></p>"
            f"<p><strong>Chemin :</strong> <code>{method} {path}</code></p>"
            f"<p><strong>Utilisateur :</strong> {user_info}</p>"
            f"<p><strong>Erreur :</strong> <pre>{str(error_message)}</pre></p>"
            f"<hr>"
            f"<p>Ceci est un message automatique du systeme de surveillance QMS.</p>"
        )

        msg = Message(subject=subject, recipients=[recipient], sender=sender)
        msg.body = text_body
        msg.html = html_body

        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info("Email incident simule (Ref: %s)", request_id)
            return True

        mail.send(msg)
        logger.info("Email incident envoye (Ref: %s)", request_id)
        return True
    except Exception:
        logger.exception("Echec email incident (Ref: %s)", request_id)
        return False
def send_email_notification_task(email, name, category, message, urgence='normale'):
    """
    Tâche d'envoi d'email pour les notifications de la plateforme.
    Formatte le message selon la catégorie et l'urgence.
    """
    try:
        from app import mail
        from flask_mail import Message

        subject = f"Alerte QMS — {category.upper()} — {urgence.upper()}"
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@qmsplatform.ma')

        # Construction du corps du mail
        html_body = f"""
        <div style='font-family: sans-serif; padding: 20px; border: 1px solid #eee;'>
            <h2 style='color: #e63946;'>Notification QMS</h2>
            <p>Bonjour {name},</p>
            <p style='background: #f8f9fa; padding: 15px; border-left: 4px solid #e63946;'>
                <strong>Message :</strong> {message}
            </p>
            <p style='font-size: 0.8rem; color: #666;'>
                Catégorie : {category} | Priorité : {urgence}<br>
                Ceci est un message automatique de QMS Platform.
            </p>
        </div>
        """

        msg = Message(subject=subject, recipients=[email], sender=sender)
        msg.html = html_body
        
        if current_app.config.get('MAIL_SUPPRESS_SEND', False):
            logger.info("Email notification simule pour %s (Cat: %s)", email, category)
            return True

        mail.send(msg)
        logger.info("Email notification envoye a %s (Cat: %s)", email, category)
        return True
    except Exception:
        logger.exception("Erreur envoi email notification a %s", email)
        return False
