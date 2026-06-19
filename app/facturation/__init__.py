from flask import Blueprint
facturation = Blueprint('facturation', __name__, template_folder='templates')
from . import routes
