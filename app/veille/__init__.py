from flask import Blueprint
veille = Blueprint('veille', __name__, template_folder='templates')
from . import routes
