from flask import Blueprint

blueprint = Blueprint('formations', __name__, template_folder='templates')

from . import routes
