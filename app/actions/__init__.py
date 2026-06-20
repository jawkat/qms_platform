from flask_smorest import Blueprint
blueprint = Blueprint('actions', __name__, template_folder='templates', description='Gestion des actions correctives')
from . import routes
