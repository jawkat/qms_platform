from flask import Blueprint
entreprises = Blueprint('entreprises', __name__, template_folder='templates')
from . import routes
