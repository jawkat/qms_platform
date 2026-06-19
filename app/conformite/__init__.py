from flask import Blueprint
blueprint = Blueprint('conformite', __name__, template_folder='templates')
from . import routes
