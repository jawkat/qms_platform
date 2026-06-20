from flask_smorest import Blueprint
blueprint = Blueprint('indicateurs', __name__, template_folder='templates', description='Suivi des indicateurs de performance')
from . import routes
