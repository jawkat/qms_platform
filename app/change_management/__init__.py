from flask import Blueprint
blueprint = Blueprint('change_management', __name__, template_folder='templates')
from . import routes
