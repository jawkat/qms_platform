from flask_smorest import Blueprint
entreprises = Blueprint('entreprises', __name__, template_folder='templates', description='Gestion des entreprises clients')
from . import routes
