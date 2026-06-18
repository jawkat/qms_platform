from flask import Blueprint
secteur = Blueprint('secteur', __name__, template_folder='templates')
from . import routes
