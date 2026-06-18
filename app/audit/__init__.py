from flask import Blueprint
blueprint = Blueprint('audit', __name__, template_folder='templates')
from . import routes
