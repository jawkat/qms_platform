from flask import Blueprint
blueprint = Blueprint('ishikawa', __name__, template_folder='templates')
from . import routes
