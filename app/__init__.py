# =============================================================================
# QMS Platform — Application Factory (Refactored)
# =============================================================================
import os
from flask import Flask
from dotenv import load_dotenv

# On ré-exporte les extensions pour maintenir la compatibilité avec "from app import db"
from .extensions import db, migrate, login_manager, csrf, mail, api
from .blueprints_registry import register_blueprints
from .errors import register_error_handlers
from .hooks import register_hooks

load_dotenv()

def create_app(config_object='config.Config'):
    """
    Factory pattern — Crée et configure l'application Flask.
    Accepts an optional config_object for testing (e.g. config.TestConfig).
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # 1. Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    api.init_app(app)

    login_manager.login_view = 'users.login'
    login_manager.login_message = 'Veuillez vous connecter pour acceder a cette page.'

    # 2. Système multi-tenancy & Audit Trail
    from app.utils.tenant_scope import init_tenant_scope
    from app.utils.audit_trail import init_audit_trail
    init_tenant_scope(app)
    init_audit_trail(app)

    # 3. Système de plugins modulaires
    from app.core import register_all_modules, plugin_manager
    register_all_modules()
    app.plugin_manager = plugin_manager

    # 4. User loader pour Flask-Login
    from app.models import Utilisateur
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    # 5. Enregistrement des composants (Blueprints, Erreurs, Hooks)
    register_blueprints(app, api)
    register_error_handlers(app)
    register_hooks(app)

    # 6. Context processor pour le sidebar et variables globales
    from app.context_processors import inject_globals
    app.context_processor(inject_globals)

    return app
