from flask_smorest import Blueprint
blueprint = Blueprint('objectifs', __name__, template_folder='templates', description='Pilotage des objectifs stratégiques')
from . import routes
