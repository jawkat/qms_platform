from flask import render_template, redirect, url_for, session, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise
from app.main import main
from app.utils.domaine_switch import set_domaine_actif


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.tableau_de_bord'))
    return render_template('landing.html')


@main.route('/tableau-de-bord')
@login_required
def tableau_de_bord():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    domaine = session.get('domaine_actif', 'hse')
    return render_template('main/dashboard.html', entreprise=entreprise, domaine=domaine)


@main.route('/switch-domaine/<domaine>')
@login_required
def switch_domaine(domaine):
    if domaine not in ('hse', 'qualite'):
        abort(400)
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    modules = entreprise.modules_actifs or ['hse']
    if domaine not in modules:
        abort(403)
    set_domaine_actif(domaine)
    return redirect(request.referrer or url_for('main.tableau_de_bord'))
