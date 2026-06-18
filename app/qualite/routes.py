from flask import render_template, session, abort
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise
from app.qualite import blueprint


def _check_qualite_access():
    """Verifie que l'entreprise a le module qualite et que le domaine actif est qualite."""
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'qualite' not in (entreprise.modules_actifs or []):
        abort(403)
    if session.get('domaine_actif') != 'qualite':
        abort(403)


@blueprint.route('/')
@login_required
def tableau_de_bord():
    _check_qualite_access()
    return render_template('qualite/tableau_de_bord.html')


@blueprint.route('/risques')
@login_required
def risques():
    _check_qualite_access()
    return render_template('qualite/risques.html')


@blueprint.route('/haccp')
@login_required
def haccp():
    _check_qualite_access()
    return render_template('qualite/haccp.html')


@blueprint.route('/clients')
@login_required
def clients():
    _check_qualite_access()
    return render_template('qualite/clients.html')


@blueprint.route('/fournisseurs')
@login_required
def fournisseurs():
    _check_qualite_access()
    return render_template('qualite/fournisseurs.html')


@blueprint.route('/formations')
@login_required
def formations():
    _check_qualite_access()
    return render_template('qualite/formations.html')


@blueprint.route('/equipements')
@login_required
def equipements():
    _check_qualite_access()
    return render_template('qualite/equipements.html')


@blueprint.route('/controle')
@login_required
def controle():
    _check_qualite_access()
    return render_template('qualite/controle.html')


@blueprint.route('/revue')
@login_required
def revue():
    _check_qualite_access()
    return render_template('qualite/revue.html')


@blueprint.route('/nonconformites')
@login_required
def nonconformites():
    _check_qualite_access()
    return render_template('qualite/nonconformites.html')
