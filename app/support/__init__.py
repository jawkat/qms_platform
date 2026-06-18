from flask import Blueprint
support = Blueprint('support', __name__, template_folder='templates')
from . import routes
