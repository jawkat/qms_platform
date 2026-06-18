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

    app.register_blueprint(main_bp)
    app.register_blueprint(entreprises_bp)
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(actions_bp, url_prefix='/actions')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(conformite_bp)
    app.register_blueprint(qualite_bp, url_prefix='/qualite')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(support_bp)
    app.register_blueprint(textes_bp, url_prefix='/textes')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(indicateurs_bp, url_prefix='/indicateurs')

    from app.context_processors import inject_globals
    app.context_processor(inject_globals)

    return app
