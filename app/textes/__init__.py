from flask import Blueprint
textes = Blueprint('textes', __name__, template_folder='templates')
from . import routes
from . import import_routes
