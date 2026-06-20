from flask_smorest import Blueprint
main = Blueprint('main', __name__, template_folder='templates', description='Pages principales et tableau de bord')
from . import routes
