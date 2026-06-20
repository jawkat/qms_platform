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
        if req.method in ('GET', 'HEAD', 'OPTIONS'):
            return
        whitelist = ('admin.', 'facturation.', 'users.logout', 'users.login', 'static')
        ep = req.endpoint or ''
        if any(ep.startswith(p) or ep == p for p in whitelist):
            return
        # Use session to avoid multiple DB lookups if needed, but for now simple query
        entreprise = db.session.get(Entreprise, current_user.entreprise_id)
        if not entreprise:
            return
        lifecycle = get_enterprise_lifecycle_status(entreprise)
        pay_status = get_payment_status(entreprise)
        if lifecycle in BLOCKED_LIFECYCLE_STATES or pay_status == 'expired':
            flash(
                'Votre abonnement est expiré. Cette action est bloquée. '
                'Merci de régulariser votre paiement.',
                'danger',
            )
            return redirect(url_for('facturation.index'))
