from flask_smorest import Blueprint

demo = Blueprint('demo', __name__, template_folder='templates')

from . import routes
