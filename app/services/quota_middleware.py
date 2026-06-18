from functools import wraps
from flask import jsonify, flash, redirect, url_for
from flask_login import current_user
from app.services.subscription_service import (
    get_user_limit_status, get_action_limit_status,
    get_documents_limit_status, get_storage_limit_status,
    ensure_enterprise_operation_allowed,
)
from app.models import Entreprise

def check_quota(entity_type='actions'):
    """Decorator that checks subscription quotas before creating entities."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            entreprise = Entreprise.query.get(current_user.entreprise_id)
            if not entreprise:
                return jsonify({'success': False, 'error': 'Entreprise not found'}), 400
            
            allowed, msg, _ = ensure_enterprise_operation_allowed(entreprise, entity_type)
            if not allowed:
                return jsonify({'success': False, 'error': msg}), 403
            
            if entity_type == 'users':
                reached, current, limit, plan = get_user_limit_status(entreprise.id)
            elif entity_type == 'actions':
                reached, current, limit, plan = get_action_limit_status(entreprise.id)
            elif entity_type == 'documents':
                reached, current, limit, plan = get_documents_limit_status(entreprise.id)
            else:
                reached = False
            
            if reached:
                return jsonify({
                    'success': False,
                    'error': f'Limite atteinte ({current}/{limit}) sur votre plan {plan}. Veuillez migrer vers un plan superieur.'
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator
