from flask import Blueprint
blueprint = Blueprint('haccp', __name__, template_folder='templates')
from . import routes
