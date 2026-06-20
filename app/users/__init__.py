from flask_smorest import Blueprint
users = Blueprint('users', __name__, template_folder='templates', description='Gestion des utilisateurs et authentification')
from . import routes
