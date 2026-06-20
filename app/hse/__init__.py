from flask_smorest import Blueprint
blueprint = Blueprint('hse', __name__, template_folder='templates', description='Module HSE (Hygiène, Sécurité, Environnement)')
from . import routes
