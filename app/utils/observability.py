import logging
import uuid
import json
from contextvars import ContextVar
from flask import has_request_context, request


_REQUEST_ID = ContextVar('request_id', default='-')


class RequestContextLogFilter(logging.Filter):
    """Inject request-scoped fields into log records."""

    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = _REQUEST_ID.get() or '-'
        if not hasattr(record, 'tenant_id'):
            record.tenant_id = '-'
        if not hasattr(record, 'user_id'):
            record.user_id = '-'
        return True


class SafeExtraFormatter(logging.Formatter):
    """Formatter that tolerates missing extra fields."""

    def format(self, record):
        for attr in ('request_id', 'tenant_id', 'user_id'):
            if not hasattr(record, attr):
                setattr(record, attr, '-')
        return super().format(record)


def get_request_id():
    return _REQUEST_ID.get() or '-'


def set_request_id(value=None):
    rid = value or str(uuid.uuid4())
    _REQUEST_ID.set(rid)
    return rid


def clear_request_id():
    _REQUEST_ID.set('-')


def configure_observability(app):
    """Configure application-wide structured logging with request correlation."""
    level_name = app.config.get('LOG_LEVEL', 'INFO')
    level = getattr(logging, str(level_name).upper(), logging.INFO)

    formatter = SafeExtraFormatter(
        '%(asctime)s %(levelname)s request_id=%(request_id)s '
        'tenant_id=%(tenant_id)s user_id=%(user_id)s %(name)s: %(message)s'
    )
    request_filter = RequestContextLogFilter()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.addFilter(request_filter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            has_filter = any(isinstance(f, RequestContextLogFilter) for f in handler.filters)
            if not has_filter:
                handler.addFilter(request_filter)
            handler.setFormatter(formatter)

    app.logger.setLevel(level)


def log_business_event(logger, event_name, tenant_id='-', user_id='-', level='info', **details):
    """Emit a structured business event log with request correlation fields."""
    payload = {'event': event_name}
    payload.update(details or {})

    log_method = getattr(logger, level, logger.info)
    log_method(
        "business_event %s",
        json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str),
        extra={
            'request_id': get_request_id(),
            'tenant_id': tenant_id or '-',
            'user_id': user_id or '-',
        },
    )

    # Persist the business event in JournalSecurite to power admin dashboards.
    ip_addr = request.remote_addr if has_request_context() else None
    user_agent = None
    if has_request_context():
        user_agent = request.headers.get('User-Agent')

    action_code = f"biz:{(event_name or '').strip()}"[:50]
    persisted_user_id = user_id if isinstance(user_id, int) else None
    record_security_event(
        type_action=action_code,
        details=payload,
        utilisateur_id=persisted_user_id,
        adresse_ip=ip_addr,
        navigateur=user_agent,
    )


def record_security_event(
    type_action,
    details=None,
    utilisateur_id=None,
    adresse_ip=None,
    navigateur=None,
):
    """Persist a security/incident event into JournalSecurite.

    This helper is best-effort and must never break request handling.
    """
    try:
        from app import db
        from app.models import JournalSecurite

        event = JournalSecurite(
            utilisateur_id=utilisateur_id,
            type_action=type_action,
            adresse_ip=adresse_ip,
            navigateur=navigateur,
            details=details or {},
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        logging.getLogger(__name__).exception(
            "security_event_persist_failed type_action=%s",
            type_action,
        )
