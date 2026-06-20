from flask_smorest import Blueprint
blueprint = Blueprint('documents', __name__, template_folder='templates', description='GED (Gestion Électronique des Documents)')
from . import routes
