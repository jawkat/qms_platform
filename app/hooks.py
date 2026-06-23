from flask import render_template, request as req, flash, redirect, url_for
from flask_login import current_user
from app.extensions import db

def register_hooks(app):
    @app.before_request
    def set_tenant():
        if current_user.is_authenticated and current_user.entreprise_id:
            from app.utils.tenant_scope import set_current_entreprise
            is_admin = current_user.role and current_user.role.est_systeme
            set_current_entreprise(current_user.entreprise_id, is_admin)

    @app.teardown_request
    def clear_tenant(exception=None):
        from app.utils.tenant_scope import clear_current_entreprise
        clear_current_entreprise()

    @app.before_request
    def set_request_id():
        from app.utils.observability import set_request_id
        set_request_id()

    @app.before_request
    def check_subscription_block():
        from app.models import Entreprise
        from app.services.subscription_service import (
            get_enterprise_lifecycle_status, get_payment_status,
            BLOCKED_LIFECYCLE_STATES,
        )
        if not current_user.is_authenticated:
            return
        if current_user.role and current_user.role.est_systeme:
            return
        if req.method in ('HEAD', 'OPTIONS'):
            return
        whitelist = ('admin.', 'facturation.', 'users.logout', 'users.login', 'static', 'main.suspended')
        ep = req.endpoint or ''
        if any(ep.startswith(p) or ep == p for p in whitelist):
            return
        entreprise = db.session.get(Entreprise, current_user.entreprise_id)
        if not entreprise:
            return
        lifecycle = get_enterprise_lifecycle_status(entreprise)
        pay_status = get_payment_status(entreprise)
        if lifecycle in BLOCKED_LIFECYCLE_STATES or pay_status == 'expired':
            return render_template('main/suspended.html', entreprise=entreprise, lifecycle=lifecycle), 403
