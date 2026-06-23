"""
QMS Platform — Utilitaires de notifications
=============================================
Ce module fournit :

  - ``create_notification()``          : wrapper legacy → délègue à NotificationService
  - ``notify_action()``                : décorateur pour notifier après une action
  - ``notify_users()``                 : notifier une liste d'utilisateurs
  - ``send_account_created_email()``   : email de création de compte
  - ``send_password_reset_email()``    : email de réinitialisation de mot de passe
  - ``send_action_reminder_email()``   : email de rappel d'action corrective
  - ``send_incident_email()``          : email d'incident technique (500)
  - ``send_email_notification_task()`` : tâche d'envoi générique (appelée par RQ)

Mapping de types
----------------
Les fonctions ``create_notification()`` acceptent un paramètre ``type``
(str) qui est automatiquement mappé vers :

  - une *categorie* (hse, qualite, general, veille, support…)
  - une *urgence*   (basse, normale, haute, critique)
  - un *entite_type* pour le routage de clic (incident, action, document…)

Vous pouvez passer ``entite_type`` et ``entite_id`` explicitement pour forcer
le routage vers un enregistrement précis lors du clic sur la notification.

Exemple
-------
::

    # Via le wrapper legacy (compatible avec le code existant)
    from app.utils.notifications import create_notification
    create_notification(
        user_id=user.id,
        message="Action corrective en retard",
        type='overdue',
        entite_id=action.id,
        entite_type='action',
    )

    # Envoi d'email de compte directement
    from app.utils.notifications import send_account_created_email
    send_account_created_email(
        recipient_email=user.email,
        recipient_name=f"{user.prenom} {user.nom}",
        role_name=user.role.nom,
    )
"""
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


TYPE_CATEGORY_MAP = {
    'incident': 'hse',
    'accident': 'hse',
    'presqu_accident': 'hse',
    'overdue': 'general',
    'echeance': 'general',
    'alerte': 'general',
    'texte': 'veille',
    'info': 'general',
    'action': 'general',
    'ticket': 'support',
    'nonconformite': 'qualite',
}

TYPE_URGENCE_MAP = {
    'incident': 'haute',
    'accident': 'critique',
    'presqu_accident': 'haute',
    'overdue': 'haute',
    'echeance': 'normale',
    'alerte': 'normale',
    'texte': 'basse',
    'info': 'normale',
    'action': 'normale',
    'ticket': 'normale',
    'nonconformite': 'normale',
}

TYPE_ENTITE_TYPE_MAP = {
    'incident': 'incident',
    'accident': 'accident',
    'presqu_accident': 'presqu_accident',
    'ticket': 'ticket',
    'action': 'action',
    'nonconformite': 'nonconformite',
    'document': 'document',
    'alerte': 'alerte',
}


def create_notification(user_id, message, type='info', entite_id=None, entite_type=None):
    category = TYPE_CATEGORY_MAP.get(type, 'general')
    urgence = TYPE_URGENCE_MAP.get(type, 'normale')
    if not entite_type:
        entite_type = TYPE_ENTITE_TYPE_MAP.get(type)

    try:
        from flask import current_app
        from app.services.notification_service import NotificationService

        return NotificationService.notify(
            utilisateur_id=user_id,
            category=category,
            message=message,
            urgence=urgence,
            entite_type=entite_type,
            entite_id=entite_id,
            notification_type=type,
            skip_module_check=True,
        )
    except Exception:
        logger.exception("Erreur create_notification via NotificationService")
        return False


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
def send_email_notification_task(email, name, category, message, urgence='normale',
                                 entreprise_nom=None, user_role=None):
    """
    Tâche d'envoi d'email pour les notifications de la plateforme.
    Vérifie les préférences utilisateur avant envoi.
    """
    try:
        from app import db
        from app.models.auth import Utilisateur
        from app.models.systeme import NotificationPreference

        user = Utilisateur.query.filter_by(email=email).first()
        if user:
            prefs = NotificationPreference.query.filter_by(
                utilisateur_id=user.id, categorie=category
            ).first()
            if prefs and not prefs.email_enabled:
                logger.info("Email désactivé par l'utilisateur %s pour %s — ignoré", email, category)
                return False
        else:
            logger.info("Email %s ne correspond à aucun utilisateur — envoi autorisé (fallback)", email)

        from app import mail
        from flask_mail import Message

        subject = f"Alerte QMS — {category.upper()} — {urgence.upper()}"
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@qmsplatform.ma')

        urgence_badge = {
            'critique': ('#dc3545', 'Critique'),
            'haute': ('#fd7e14', 'Haute'),
            'normale': ('#0d6efd', 'Normale'),
            'basse': ('#6c757d', 'Basse'),
        }
        badge_color, badge_label = urgence_badge.get(urgence, ('#6c757d', urgence.capitalize()))

        entreprise_block = f"""
        <tr>
            <td style='padding: 6px 0; color: #666; font-size: 0.85rem;'>Entreprise</td>
            <td style='padding: 6px 0; font-weight: 600;'>{entreprise_nom}</td>
        </tr>""" if entreprise_nom else ''

        role_block = f"""
        <tr>
            <td style='padding: 6px 0; color: #666; font-size: 0.85rem;'>Rôle</td>
            <td style='padding: 6px 0; font-weight: 600;'>{user_role}</td>
        </tr>""" if user_role else ''

        html_body = f"""
        <div style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px;
                    overflow: hidden; border: 1px solid #e0e0e0;'>
            <div style='background: linear-gradient(135deg, #e63946 0%, #a82a33 100%);
                        padding: 24px 32px; text-align: center;'>
                <h1 style='margin: 0; color: #fff; font-size: 1.4rem;'>Notification QMS</h1>
                <span style='display: inline-block; margin-top: 8px; padding: 4px 14px;
                            background: {badge_color}; color: #fff; border-radius: 20px;
                            font-size: 0.75rem; font-weight: 600;'>{badge_label}</span>
            </div>
            <div style='padding: 24px 32px;'>
                <p style='margin: 0 0 16px 0; font-size: 1rem;'>Bonjour <strong>{name}</strong>,</p>
                <div style='background: #f8f9fa; padding: 16px; border-left: 4px solid {badge_color};
                            border-radius: 4px; margin-bottom: 20px;'>
                    <p style='margin: 0; color: #333; line-height: 1.5;'>{message}</p>
                </div>
                <table style='width: 100%; border-collapse: collapse;'>
                    {entreprise_block}
                    {role_block}
                    <tr>
                        <td style='padding: 6px 0; color: #666; font-size: 0.85rem;'>Catégorie</td>
                        <td style='padding: 6px 0; font-weight: 600;'>{category}</td>
                    </tr>
                    <tr>
                        <td style='padding: 6px 0; color: #666; font-size: 0.85rem;'>Priorité</td>
                        <td style='padding: 6px 0; font-weight: 600;'>{urgence.upper()}</td>
                    </tr>
                </table>
            </div>
            <div style='background: #f1f3f5; padding: 16px 32px; text-align: center;
                        font-size: 0.75rem; color: #868e96;'>
                Ceci est un message automatique de QMS Platform.
            </div>
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
