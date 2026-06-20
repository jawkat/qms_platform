from flask_smorest import Blueprint
blueprint = Blueprint('reclamations', __name__, template_folder='templates', description='Gestion des réclamations clients')


from . import routes
