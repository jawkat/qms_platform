from flask import current_app
from datetime import datetime


def validate_notification_ids(notification_ids):
    """
    Validate notification IDs are a list of integers or strings representing IDs.
    Returns (is_valid, error_messages).
    """
    errors = []

    if not notification_ids:
        errors.append('notification_ids list is required and cannot be empty')
        return False, errors

    if not isinstance(notification_ids, (list, tuple)):
        errors.append(f'notification_ids must be list or tuple, got {type(notification_ids)}')
        return False, errors

    if len(notification_ids) == 0:
        errors.append('notification_ids list cannot be empty')
        return False, errors

    for item in notification_ids:
        if not isinstance(item, (int, str)):
            errors.append(f'Each notification ID must be int or str, got {type(item)}')
            return False, errors

        if isinstance(item, str) and not item.isdigit():
            errors.append(f'Invalid notification ID (not numeric string): {item}')
            return False, errors

    return True, errors


def send_notifications(notification_ids):
    """
    Fetch notifications by IDs, validate, and send them.
    Returns stats dict with sent_count, failed_count, errors.
    """
    stats = {
        'notification_ids': notification_ids,
        'fetched_count': 0,
        'sent_count': 0,
        'failed_count': 0,
        'errors': [],
        'validation_failed': 0,
    }

    # Validate notification IDs
    ids_valid, ids_errors = validate_notification_ids(notification_ids)
    if not ids_valid:
        stats['validation_failed'] = len(ids_errors)
        stats['errors'].extend(ids_errors)
        return stats

    try:
        # Placeholder: fetch notifications from database
        notifications = _fetch_notifications(notification_ids)
        stats['fetched_count'] = len(notifications)

        if not notifications:
            stats['errors'].append(f'No notifications found for IDs: {notification_ids}')
            return stats

        # Validate and send each notification
        for notification in notifications:
            try:
                # Validate notification structure
                is_valid, validation_errors = _validate_notification(notification)
                if not is_valid:
                    stats['failed_count'] += 1
                    stats['errors'].extend(validation_errors)
                    continue

                # Send notification
                result = _send_single_notification(notification)
                if result['success']:
                    stats['sent_count'] += 1
                    # Mark notification as sent in DB
                    _mark_notification_sent(notification['id'])
                else:
                    stats['failed_count'] += 1
                    stats['errors'].append(result.get('error', f'Failed to send notification {notification["id"]}'))

            except Exception as e:
                stats['failed_count'] += 1
                stats['errors'].append(f'Error sending notification {notification.get("id")}: {str(e)}')
                current_app.logger.exception(f'Notification send error for {notification}')

    except Exception as e:
        stats['errors'].append(f'Notification batch failed: {str(e)}')
        current_app.logger.exception('Notification batch error')

    return stats


def _fetch_notifications(notification_ids):
    """
    Placeholder: fetch Notification objects from database.
    In real implementation, query using SQLAlchemy.
    Returns list of notification dicts with required fields.
    """
    # Example structure:
    notifications = []
    for nid in notification_ids:
        notifications.append({
            'id': nid,
            'recipient_email': f'user{nid}@example.com',
            'recipient_name': f'User {nid}',
            'subject': f'Notification {nid}',
            'message': f'This is notification {nid}',
            'type': 'email',  # or 'sms', 'in_app'
            'created_at': datetime.utcnow().isoformat(),
        })
    return notifications


def _validate_notification(notification):
    """
    Validate notification has required fields for delivery.
    Returns (is_valid, error_messages).
    """
    errors = []

    required_fields = ['id', 'recipient_email', 'type', 'subject', 'message']
    for field in required_fields:
        if field not in notification or notification[field] is None:
            errors.append(f'Notification missing required field: {field}')

    # Validate recipient email if type is email
    if notification.get('type') == 'email':
        email = notification.get('recipient_email', '')
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            errors.append(f'Invalid recipient email: {email}')

    return len(errors) == 0, errors


def _send_single_notification(notification):
    """
    Send a single notification based on its type (email, sms, in_app).
    Returns dict with success flag and optional error message.
    """
    try:
        ntype = notification.get('type', 'email')

        if ntype == 'email':
            return _send_email_notification(notification)
        elif ntype == 'sms':
            return _send_sms_notification(notification)
        elif ntype == 'in_app':
            return _send_in_app_notification(notification)
        else:
            return {'success': False, 'error': f'Unknown notification type: {ntype}'}

    except Exception as e:
        current_app.logger.exception("Erreur envoi notification")
        return {'success': False, 'error': 'Erreur interne lors de l\'envoi de la notification'}


def _send_email_notification(notification):
    """Send notification via email."""
    try:
        from flask_mail import Message, mail

        msg = Message(
            subject=notification.get('subject', 'Notification'),
            recipients=[notification.get('recipient_email')],
            body=notification.get('message', ''),
            html=f"<p>{notification.get('message', '')}</p>",
        )
        mail.send(msg)
        return {'success': True}

    except Exception as e:
        return {'success': False, 'error': f'Email send failed: {e}'}


def _send_sms_notification(notification):
    """
    Placeholder: send notification via SMS (e.g. using Twilio).
    In real implementation, integrate with SMS provider.
    """
    # Example: would use Twilio or similar
    return {'success': True}  # Placeholder


def _send_in_app_notification(notification):
    """
    Store in-app notification in database for user dashboard.
    Placeholder: would create Notification record in DB.
    """
    return {'success': True}  # Placeholder


def _mark_notification_sent(notification_id):
    """
    Update notification record to mark as sent.
    Placeholder: would update DB record with sent_at timestamp.
    """
    # In real implementation, query DB and update sent_at
    current_app.logger.debug(f'Marked notification {notification_id} as sent')
