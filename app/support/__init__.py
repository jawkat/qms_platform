from flask_smorest import Blueprint
support = Blueprint('support', __name__, template_folder='templates', description='Centre de support et tickets')
from . import routes
