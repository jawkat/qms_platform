from flask_smorest import Blueprint
blueprint = Blueprint('qualite', __name__, template_folder='templates', description='Système de Management de la Qualité')
from . import routes
