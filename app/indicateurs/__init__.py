from flask import Blueprint
blueprint = Blueprint('indicateurs', __name__, template_folder='templates')
from . import routes
