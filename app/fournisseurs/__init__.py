from flask_smorest import Blueprint
blueprint = Blueprint('fournisseurs', __name__, template_folder='templates', description='Gestion et évaluation des fournisseurs')


from . import routes
