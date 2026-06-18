from flask import Blueprint
blueprint = Blueprint('documents', __name__, template_folder='templates')
from . import routes
