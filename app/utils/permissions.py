from functools import wraps
from flask import abort, current_app, flash, request
from flask_login import current_user

from app.extensions import db
from app.utils.observability import get_request_id, record_security_event
from app.utils.permission_catalog import is_known_permission


def has_permission(permission_code):
    """
    Décorateur qui vérifie si l'utilisateur connecté a la permission requise.
    Usage: @require_permission('users.create')
    L'administrateur système a toujours accès complet.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_known_permission(permission_code):
                current_app.logger.error(
                    "Permission inconnue utilisee dans un decorateur: %s",
                    permission_code,
                )
                abort(500)

            if not current_user.is_authenticated:
                abort(401)

            # Un role systeme a toujours acces.
            if current_user.role and current_user.role.est_systeme:
                return f(*args, **kwargs)

            # Vérifier les permissions dans le contexte de l'entreprise
            if not current_user.has_permission(permission_code, current_user.entreprise_id):
                request_id = get_request_id()
                current_app.logger.warning(
                    (
                        "rbac_denied permission=%s endpoint=%s method=%s "
                        "remote_addr=%s"
                    ),
                    permission_code,
                    request.endpoint,
                    request.method,
                    request.remote_addr,
                    extra={
                        'request_id': request_id,
                        'tenant_id': current_user.entreprise_id or '-',
                        'user_id': current_user.id or '-',
                    },
                )
                record_security_event(
                    type_action='rbac_denied',
                    utilisateur_id=current_user.id,
                    adresse_ip=request.remote_addr,
                    navigateur=request.headers.get('User-Agent'),
                    details={
                        'request_id': request_id,
                        'permission': permission_code,
                        'endpoint': request.endpoint,
                        'method': request.method,
                    },
                )
                flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'error')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def module_access_required(module_name, *permissions):
    """Vérifie que l'entreprise de l'utilisateur a activé le module ET que l'utilisateur a la permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            from app import db
            from app.models.entreprise import Entreprise
            entreprise = db.session.get(Entreprise, current_user.entreprise_id)
            if not entreprise or module_name not in (entreprise.modules_actifs or []):
                abort(403)

            if permissions:
                ok = False
                for code in permissions:
                    if current_user.has_permission(code, current_user.entreprise_id):
                        ok = True
                        break
                if not ok:
                    abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def system_admin_required(f):
    """Décorateur imposant un administrateur système pour une action sensible."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        role = getattr(current_user, 'role', None)
        is_system_admin = bool(role and role.est_systeme)
        if not is_system_admin:
            flash('Cette opération est réservée à l\'administrateur système.', 'error')
            abort(403)

        return f(*args, **kwargs)

    return decorated_function




def access_required(permission=None, module=None):
    """
    Décorateur unique qui vérifie en une ligne :
      1. Authentification (remplace @login_required)
      2. Permission (remplace @has_permission)
      3. Activation de module (remplace @module_access_required)

    Usage::

        @access_required(permission='formations.voir')
        @access_required(permission='haccp.gerer_ccp', module='haccp')
        @access_required(module='haccp')  # vérifie juste le module
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            if module:
                from app.models.entreprise import Entreprise
                entreprise = db.session.get(Entreprise, current_user.entreprise_id)
                if not entreprise or module not in (entreprise.modules_actifs or []):
                    abort(403)

            if permission:
                if not is_known_permission(permission):
                    current_app.logger.error(
                        "Permission inconnue utilisee: %s", permission,
                    )
                    abort(500)

                if current_user.role and current_user.role.est_systeme:
                    return f(*args, **kwargs)

                if not current_user.has_permission(permission, current_user.entreprise_id):
                    request_id = get_request_id()
                    current_app.logger.warning(
                        (
                            "rbac_denied permission=%s endpoint=%s method=%s "
                            "remote_addr=%s"
                        ),
                        permission,
                        request.endpoint,
                        request.method,
                        request.remote_addr,
                        extra={
                            'request_id': request_id,
                            'tenant_id': current_user.entreprise_id or '-',
                            'user_id': current_user.id or '-',
                        },
                    )
                    record_security_event(
                        type_action='rbac_denied',
                        utilisateur_id=current_user.id,
                        adresse_ip=request.remote_addr,
                        navigateur=request.headers.get('User-Agent'),
                        details={
                            'request_id': request_id,
                            'permission': permission,
                            'endpoint': request.endpoint,
                            'method': request.method,
                        },
                    )
                    flash('Vous n\'avez pas la permission d\'accéder à cette page.', 'error')
                    abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# def user_has_permission(user, permission_code):
#     """
#     Fonction utilitaire permettant de vérifier une permission pour un
#     objet utilisateur (compatibilité avec l'ancien `has_permission(user, ...)`).
#     Retourne True/False.
#     """
#     if not user or not getattr(user, 'is_authenticated', False):
#         return False
#     if not hasattr(user, 'has_permission'):
#         # Ancien modèle: vérifier via role/permissions
#         role = getattr(user, 'role', None)
#         if not role:
#             return False
#         for rp in getattr(role, 'permissions', []):
#             perm = getattr(rp, 'permission', None)
#             if perm and getattr(rp, 'autorise', False) and getattr(perm, 'code', None) == permission_code:
#                 return True
#         return False

#     return user.has_permission(permission_code)
