from flask_smorest import Blueprint
blueprint = Blueprint('haccp', __name__, template_folder='templates', description='Gestion de la sécurité alimentaire (HACCP/CCP)')
from . import routes
