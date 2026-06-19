from flask import current_app, render_template
from flask_mail import Message
from app import mail


def send_async_email(subject, recipients, html, sender=None):
    try:
        msg = Message(
            subject=subject,
            recipients=recipients if isinstance(recipients, list) else [recipients],
            html=html,
            sender=sender or current_app.config.get('MAIL_DEFAULT_SENDER'),
        )
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {e}')


def send_action_reminder_email(user_email, user_name, action):
    html = render_template('emails/action_reminder.html', action=action, user_name=user_name)
    send_async_email(
        subject=f'Rappel: Action corrective #{action.id}',
        recipients=[user_email],
        html=html,
    )


def send_ticket_reply_email(ticket, recipient_email, message):
    html = render_template('emails/ticket_reply.html', ticket=ticket, message=message)
    send_async_email(
        subject=f'Réponse à votre ticket #{ticket.reference}',
        recipients=[recipient_email],
        html=html,
    )
