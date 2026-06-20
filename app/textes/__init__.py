from flask_smorest import Blueprint
textes = Blueprint('textes', __name__, template_folder='templates')
from . import routes
