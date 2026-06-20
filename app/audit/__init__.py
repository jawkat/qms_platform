from flask_smorest import Blueprint
blueprint = Blueprint('audit', __name__, template_folder='templates', description='Gestion des audits et checklists')
from . import routes
