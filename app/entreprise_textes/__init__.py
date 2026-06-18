from flask import Blueprint

entreprise_textes = Blueprint('entreprise_textes', __name__,
                              url_prefix='/entreprise-textes',
                              template_folder='templates')

from app.entreprise_textes import routes
