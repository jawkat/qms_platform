from flask import Blueprint
blueprint = Blueprint('conformite', __name__, url_prefix='/conformite', template_folder='templates')
from . import routes
