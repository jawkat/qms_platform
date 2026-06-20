from flask_smorest import Blueprint
admin = Blueprint('admin', __name__, template_folder='templates', description='Administration globale et gestion multi-tenant')
from . import routes
