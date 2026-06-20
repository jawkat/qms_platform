from flask_smorest import Blueprint
blueprint = Blueprint('workflow_engine', __name__, template_folder='templates')
from . import routes
