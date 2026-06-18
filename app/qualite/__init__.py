from flask import Blueprint
blueprint = Blueprint('qualite', __name__, template_folder='templates')
from . import routes
