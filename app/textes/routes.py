from flask import render_template
from flask_login import login_required
from app.textes import textes


@textes.route('/')
@login_required
def index():
    return render_template('textes/index.html')
