from flask_smorest import Blueprint
blueprint = Blueprint('nonconformites', __name__, template_folder='templates', description='Gestion des non-conformités')
from . import routes
