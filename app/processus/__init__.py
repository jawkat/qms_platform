from flask_smorest import Blueprint
blueprint = Blueprint('processus', __name__, template_folder='templates')
from . import routes
