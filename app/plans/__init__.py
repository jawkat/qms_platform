from flask_smorest import Blueprint
plans = Blueprint('plans', __name__, template_folder='templates')
from . import routes
