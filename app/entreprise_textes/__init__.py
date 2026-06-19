from flask import Blueprint

entreprise_textes = Blueprint('entreprise_textes', __name__, template_folder='templates')

from app.entreprise_textes import routes
