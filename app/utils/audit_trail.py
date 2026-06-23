import logging
from datetime import datetime
from flask import has_request_context, request
from flask_login import current_user
from app import db
from app.models.systeme import JournalSecurite

logger = logging.getLogger(__name__)

_TRACKED_MODELS = set()
_IGNORED_COLUMNS = {'date_creation', 'date_modification', 'updated_at'}
_IGNORED_MODELS = {'Notification', 'JournalSecurite'}


def init_audit_trail(app):
    """Enregistre les listeners SQLAlchemy pour tracker les modifications."""
    @db.event.listens_for(db.Session, 'before_flush')
    def _before_flush(session, flush_context, instances):
        if not has_request_context():
            return

        user_id = None
        try:
            if current_user.is_authenticated:
                user_id = current_user.id
        except Exception:
            pass

        ip_addr = request.remote_addr if has_request_context() else None
        user_agent = request.headers.get('User-Agent') if has_request_context() else None

        for obj in session.new:
            if type(obj).__name__ not in _IGNORED_MODELS:
                _log_change('CREATE', obj, None, None, user_id, ip_addr, user_agent)

        for obj in session.dirty:
            if type(obj).__name__ in _IGNORED_MODELS:
                continue
            hist = db.inspect(obj).committed_state
            for attr in db.inspect(obj).mapper.column_attrs:
                col_name = attr.key
                if col_name in _IGNORED_COLUMNS:
                    continue
                old_val = hist.get(attr.key)
                new_val = getattr(obj, attr.key, None)
                if old_val != new_val:
                    _log_change('UPDATE', obj, col_name, (old_val, new_val), user_id, ip_addr, user_agent)

        for obj in session.deleted:
            if type(obj).__name__ not in _IGNORED_MODELS:
                _log_change('DELETE', obj, None, None, user_id, ip_addr, user_agent)


def _log_change(action_type, obj, field, change, user_id, ip_addr, user_agent):
    """Enregistre un changement dans JournalSecurite."""
    try:
        model_name = type(obj).__name__
        obj_id = getattr(obj, 'id', None)
        entreprise_id = getattr(obj, 'entreprise_id', None)

        details = {
            'model': model_name,
            'object_id': obj_id,
            'action': action_type,
        }
        if field:
            old_val, new_val = change
            details['field'] = field
            details['old'] = str(old_val)[:500] if old_val is not None else None
            details['new'] = str(new_val)[:500] if new_val is not None else None

        event = JournalSecurite(
            utilisateur_id=user_id,
            type_action=f'crud:{action_type.lower()}:{model_name.lower()}',
            adresse_ip=ip_addr,
            navigateur=user_agent,
            details=details,
        )
        db.session.add(event)
    except Exception:
        logger.exception('audit_trail_log_failed')
