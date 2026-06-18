from flask import Blueprint
blueprint = Blueprint('actions', __name__, template_folder='templates')
from . import routes
