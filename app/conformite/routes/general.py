from flask import render_template
from flask_login import login_required, current_user
from app import db
from app.models import EvaluationArticle, EntrepriseTexte
from app.conformite import blueprint


@blueprint.route('/')
@blueprint.route('/index')
@login_required
def index():
    textes = EntrepriseTexte.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    return render_template('conformite/index.html', textes=textes)
