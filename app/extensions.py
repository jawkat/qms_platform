from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

from flask_smorest import Api, Blueprint
from webargs.flaskparser import FlaskParser

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
api = Api()


# ---------------------------------------------------------------------------
# Patch Flask-Smorest's Blueprint ARGUMENTS_PARSER to inject db.session
# into marshmallow schema context, enabling load_instance=True deserialization.
# ---------------------------------------------------------------------------

class _SessionParser(FlaskParser):
    """Parser that injects db.session into schema context before load()."""

    def _process_location_data(
        self, location_data, schema, req, location, unknown, validators
    ):
        from app.extensions import db as _db
        schema._session = _db.session
        return super()._process_location_data(
            location_data, schema, req, location, unknown, validators,
        )


Blueprint.ARGUMENTS_PARSER = _SessionParser()

