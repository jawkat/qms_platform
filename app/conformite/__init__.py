from flask_smorest import Blueprint
blueprint = Blueprint('conformite', __name__, template_folder='templates', description='Veille et Conformité Réglementaire')
from . import routes
