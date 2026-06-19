from flask import Blueprint

blueprint = Blueprint('fournisseurs', __name__, template_folder='templates')

from . import routes
