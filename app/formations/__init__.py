from flask_smorest import Blueprint
blueprint = Blueprint('formations', __name__, template_folder='templates', description='Gestion des formations et compétences')


from . import routes
