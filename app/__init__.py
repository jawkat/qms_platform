# =============================================================================
# QMS Platform — Application Factory
# =============================================================================
"""
Factory pattern pour la création de l'application Flask.

Cette fonction create_app() est le point d'entrée principal de l'application.
Elle initialise :
1. Les extensions Flask (SQLAlchemy, Migrate, Login, Mail, CSRF)
2. Le système de plugins modulaires (PluginManager)
3. Le système multi-tenancy (ContextVar + SQLAlchemy events)
4. L'audit trail automatique
5. Tous les blueprints métier
6. Le context processor pour le sidebar

Usage :
    from app import create_app
    app = create_app()
    app.run()

Auteur : QMS Platform Team
Version : 2.0.0 (modular architecture)
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Extensions Flask (initialisées avant create_app)
# =============================================================================
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()


def create_app():
    """
    Factory pattern — Crée et configure l'application Flask.

    Cette fonction est appelée :
    - Par run.py pour démarrer le serveur
    - Par les tests pour créer une instance de test
    - Par gunicorn via le module wsgi

    Returns:
        Flask: Instance configurée de l'application
    """
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # -------------------------------------------------------------------------
    # 1. Initialisation des extensions
    # -------------------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'users.login'
    login_manager.login_message = 'Veuillez vous connecter pour acceder a cette page.'

    # -------------------------------------------------------------------------
    # 2. Système multi-tenancy (ContextVar + SQLAlchemy events)
    # -------------------------------------------------------------------------
    from app.utils.tenant_scope import init_tenant_scope
    init_tenant_scope(app)

    # -------------------------------------------------------------------------
    # 3. Audit trail automatique (SQLAlchemy before_flush listener)
    # -------------------------------------------------------------------------
    from app.utils.audit_trail import init_audit_trail
    init_audit_trail(app)

    # -------------------------------------------------------------------------
    # 4. Système de plugins modulaires
    # -------------------------------------------------------------------------
    from app.core import register_all_modules, plugin_manager
    register_all_modules()

    # Rendre le plugin_manager disponible dans le contexte de l'app
    app.plugin_manager = plugin_manager

    # -------------------------------------------------------------------------
    # 5. User loader pour Flask-Login
    # -------------------------------------------------------------------------
    from app.models import Utilisateur

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    # -------------------------------------------------------------------------
    # 6. Enregistrement des blueprints
    # -------------------------------------------------------------------------
    _register_blueprints(app)

    # -------------------------------------------------------------------------
    # 7. Before-request : mise en place du contexte tenant
    # -------------------------------------------------------------------------
    @app.before_request
    def set_tenant():
        from flask_login import current_user
        if current_user.is_authenticated and current_user.entreprise_id:
            from app.utils.tenant_scope import set_current_entreprise
            is_admin = current_user.role and current_user.role.est_systeme
            set_current_entreprise(current_user.entreprise_id, is_admin)

    # -------------------------------------------------------------------------
    # 8. Context processor global (sidebar, notifications, etc.)
    # -------------------------------------------------------------------------
    from app.context_processors import inject_globals
    app.context_processor(inject_globals)

    return app


def _register_blueprints(app):
    """
    Enregistre tous les blueprints de l'application.

    Chaque blueprint correspond à un module métier. L'ordre d'enregistrement
    n'a pas d'impact sur le fonctionnement — Flask résout les routes par
    le nom du blueprint + endpoint.

    Architecture modulaire :
    - Les blueprints core (main, users, admin) sont toujours enregistrés
    - Les blueprints métier (haccp, hse, qualite) sont toujours enregistrés
      mais l'accès est contrôlé par le plugin_manager (module activation)
    """
    # --- Core (toujours actifs) ---
    from .main import main as main_bp
    from .users import users as users_bp
    from .admin import admin as admin_bp
    from .support import support as support_bp
    from .entreprises import entreprises as entreprises_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(support_bp, url_prefix='/support')
    app.register_blueprint(entreprises_bp, url_prefix='/entreprises')

    # --- GED & Documents ---
    from .documents import blueprint as documents_bp
    app.register_blueprint(documents_bp, url_prefix='/documents')

    # --- Qualité ---
    from .actions import blueprint as actions_bp
    from .audit import blueprint as audit_bp
    from .indicateurs import blueprint as indicateurs_bp
    from .qualite import blueprint as qualite_bp
    from .nonconformites import blueprint as nonconformites_bp
    from .reclamations import blueprint as reclamations_bp
    from .fournisseurs import blueprint as fournisseurs_bp
    from .formations import blueprint as formations_bp
    from .ishikawa import blueprint as ishikawa_bp

    app.register_blueprint(actions_bp, url_prefix='/actions')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(indicateurs_bp, url_prefix='/indicateurs')
    app.register_blueprint(qualite_bp, url_prefix='/qualite')
    app.register_blueprint(nonconformites_bp, url_prefix='/nonconformites')
    app.register_blueprint(reclamations_bp, url_prefix='/reclamations')
    app.register_blueprint(fournisseurs_bp, url_prefix='/fournisseurs')
    app.register_blueprint(formations_bp, url_prefix='/formations')
    app.register_blueprint(ishikawa_bp, url_prefix='/ishikawa')

    # --- HSE ---
    from .hse import blueprint as hse_bp
    from .textes import textes as textes_bp
    from .veille import veille as veille_bp
    from .conformite import blueprint as conformite_bp
    from .secteur import secteur as secteur_bp
    from .entreprise_textes import entreprise_textes as entreprise_textes_bp

    app.register_blueprint(hse_bp, url_prefix='/hse')
    app.register_blueprint(textes_bp, url_prefix='/admin/textes')
    app.register_blueprint(veille_bp, url_prefix='/admin/veille')
    app.register_blueprint(conformite_bp, url_prefix='/conformite')
    app.register_blueprint(secteur_bp, url_prefix='/secteur')
    app.register_blueprint(entreprise_textes_bp, url_prefix='/entreprise-textes')

    # --- HACCP ---
    from .haccp import blueprint as haccp_bp
    app.register_blueprint(haccp_bp, url_prefix='/haccp')

    # --- Processus & Workflows ---
    from .processus import blueprint as processus_bp
    from .change_management import blueprint as change_management_bp
    from .workflow_engine import blueprint as workflow_engine_bp

    app.register_blueprint(processus_bp, url_prefix='/processus')
    app.register_blueprint(change_management_bp, url_prefix='/change-management')
    app.register_blueprint(workflow_engine_bp, url_prefix='/workflow-engine')

    # --- Facturation & Plans ---
    from .facturation import facturation as facturation_bp
    from .plans import plans as plans_bp

    app.register_blueprint(facturation_bp, url_prefix='/facturation')
    app.register_blueprint(plans_bp, url_prefix='/plans')

    # --- Démo ---
    from .demo import demo as demo_bp
    app.register_blueprint(demo_bp, url_prefix='/demo')

    # --- Nouveaux modules (8 modules manquants) ---
    from .environnement.routes import blueprint as environnement_bp
    from .maintenance.routes import blueprint as maintenance_bp
    from .laboratoire.routes import blueprint as laboratoire_bp
    from .planification.routes import blueprint as planification_bp
    from .reunions.routes import blueprint as reunions_bp
    from .rh_qhse.routes import blueprint as rh_qhse_bp
    from .connaissances.routes import blueprint as connaissances_bp
    from .urgences.routes import blueprint as urgences_bp

    app.register_blueprint(environnement_bp, url_prefix='/environnement')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(laboratoire_bp, url_prefix='/laboratoire')
    app.register_blueprint(planification_bp, url_prefix='/planification')
    app.register_blueprint(reunions_bp, url_prefix='/reunions')
    app.register_blueprint(rh_qhse_bp, url_prefix='/rh-qhse')
    app.register_blueprint(connaissances_bp, url_prefix='/connaissances')
    app.register_blueprint(urgences_bp, url_prefix='/urgences')
