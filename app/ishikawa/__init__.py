from flask_smorest import Blueprint
blueprint = Blueprint('ishikawa', __name__, template_folder='templates', description='Analyse des causes (Diagramme d Ishikawa)')
from . import routes
