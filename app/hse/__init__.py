from flask import Blueprint
blueprint = Blueprint('hse', __name__, template_folder='templates')
from . import routes
