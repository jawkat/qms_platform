from flask import Blueprint

blueprint = Blueprint('reclamations', __name__, template_folder='templates')

from . import routes
