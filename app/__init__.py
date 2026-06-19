import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'users.login'
    login_manager.login_message = 'Veuillez vous connecter pour acceder a cette page.'

    from app.utils.tenant_scope import init_tenant_scope
    init_tenant_scope(app)

    from app.models import Utilisateur

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    from .main import main as main_bp
    from .entreprises import entreprises as entreprises_bp
    from .users import users as users_bp
    from .actions import blueprint as actions_bp
    from .documents import blueprint as documents_bp
    from .conformite import blueprint as conformite_bp
    from .qualite import blueprint as qualite_bp
    from .admin import admin as admin_bp
    from .support import support as support_bp
    from .textes import textes as textes_bp
    from .audit import blueprint as audit_bp
    from .indicateurs import blueprint as indicateurs_bp
    from .secteur import secteur as secteur_bp
    from .entreprise_textes import entreprise_textes as entreprise_textes_bp
    from .demo import demo as demo_bp
    from .veille import veille as veille_bp
    from .haccp import blueprint as haccp_bp
    from .nonconformites import blueprint as nonconformites_bp
    from .hse import blueprint as hse_bp
    from .ishikawa import blueprint as ishikawa_bp
    from .facturation import facturation as facturation_bp
    from .plans import plans as plans_bp
    from .fournisseurs import blueprint as fournisseurs_bp
    from .formations import blueprint as formations_bp
    from .reclamations import blueprint as reclamations_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(entreprises_bp, url_prefix='/entreprises')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(actions_bp, url_prefix='/actions')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(conformite_bp)
    app.register_blueprint(qualite_bp, url_prefix='/qualite')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(support_bp, url_prefix='/support')
    app.register_blueprint(textes_bp, url_prefix='/textes')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(indicateurs_bp, url_prefix='/indicateurs')
    app.register_blueprint(secteur_bp, url_prefix='/secteur')
    app.register_blueprint(entreprise_textes_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(veille_bp, url_prefix='/veille')
    app.register_blueprint(haccp_bp, url_prefix='/haccp')
    app.register_blueprint(nonconformites_bp, url_prefix='/nonconformites')
    app.register_blueprint(hse_bp, url_prefix='/hse')
    app.register_blueprint(ishikawa_bp, url_prefix='/ishikawa')
    app.register_blueprint(facturation_bp, url_prefix='/facturation')
    app.register_blueprint(plans_bp, url_prefix='/plans')
    app.register_blueprint(fournisseurs_bp, url_prefix='/fournisseurs')
    app.register_blueprint(formations_bp, url_prefix='/formations')
    app.register_blueprint(reclamations_bp, url_prefix='/reclamations')

    @app.before_request
    def set_tenant():
        from flask_login import current_user
        if current_user.is_authenticated and current_user.entreprise_id:
            from app.utils.tenant_scope import set_current_entreprise
            is_admin = current_user.role and current_user.role.est_systeme
            set_current_entreprise(current_user.entreprise_id, is_admin)

    from app.context_processors import inject_globals
    app.context_processor(inject_globals)

    return app
