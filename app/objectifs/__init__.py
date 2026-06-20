from flask import Blueprint
blueprint = Blueprint('objectifs', __name__, template_folder='templates')
from . import routes
