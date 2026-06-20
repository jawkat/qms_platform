import time
from flask import render_template, jsonify, request as req, current_app as _app
from werkzeug.exceptions import HTTPException
from app.extensions import db

def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                from app.services.notification_service import NotificationService
                NotificationService.notify_system_admins('technique', f"404 sur {req.path} par {current_user.email}", urgence='basse')
            except Exception:
                pass
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        if isinstance(error, HTTPException):
            return error

        try:
            db.session.rollback()
        except Exception:
            pass

        from flask_login import current_user
        from app.utils.observability import get_request_id, record_security_event

        tenant_id = current_user.entreprise_id if getattr(current_user, 'is_authenticated', False) else '-'
        user_id = current_user.id if getattr(current_user, 'is_authenticated', False) else '-'
        request_id = get_request_id()

        _app.logger.exception(
            "unhandled_exception path=%s method=%s request_id=%s",
            req.path, req.method, request_id,
            extra={'request_id': request_id, 'tenant_id': tenant_id, 'user_id': user_id},
        )

        record_security_event(
            type_action='unhandled_exception',
            utilisateur_id=None if user_id == '-' else user_id,
            adresse_ip=req.remote_addr,
            navigateur=req.headers.get('User-Agent'),
            details={
                'request_id': request_id,
                'path': req.path,
                'method': req.method,
                'endpoint': req.endpoint,
                'error_type': type(error).__name__,
                'error_message': str(error),
            },
        )

        try:
            from app.services.notification_service import NotificationService
            incident_message = f"Bug applicatif ({type(error).__name__}) sur {req.method} {req.path}. Ref: {request_id}"
            NotificationService.notify_system_admins('technique', incident_message, urgence='critique')
        except Exception:
            _app.logger.exception("incident_notification_failed request_id=%s", request_id)

        accepts_json = (
            req.is_json
            or req.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or 'application/json' in (req.headers.get('Accept', ''))
        )
        if accepts_json:
            return jsonify({'success': False, 'error': 'Erreur interne', 'request_id': request_id}), 500
        return render_template('errors/500.html', request_id=request_id), 500
