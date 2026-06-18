from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app import db

from app.models import TexteReglementaire, TexteVersion, Article, Secteur, ExigenceType
from . import secteur
from app.utils.permissions import has_permission
from flask import jsonify


@secteur.route('/')
@login_required
@has_permission('secteur.voir')
def liste_secteurs():
    """Liste des secteurs"""
    secteurs_list = Secteur.query.all()
    return render_template('secteur/liste.html', secteurs=secteurs_list)   



@secteur.route('/<int:secteur_id>')
@login_required
@has_permission('secteur.voir')
def consulter_secteur(secteur_id):
    """Consulter un secteur"""
    secteur = Secteur.query.get_or_404(secteur_id)
    return render_template('secteur/consulter.html', secteur=secteur)


@secteur.route('/admin/textes')
@login_required
@has_permission('secteur.gerer_textes')
def admin_textes():
    """Admin interface: list all textes and their linked secteurs"""
    textes = TexteReglementaire.query.order_by(TexteReglementaire.titre).all()
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('secteur/admin_textes.html', textes=textes, secteurs=secteurs)


@secteur.route('/admin/textes/<int:texte_id>/edit_secteurs', methods=['GET'])
@login_required
@has_permission('secteur.gerer_textes')
def edit_textes_secteurs_form(texte_id):
    """Return partial form to edit secteurs for a texte (used by modal AJAX)"""
    t = TexteReglementaire.query.get_or_404(texte_id)
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    # prepare selected ids
    selected = [s.id for s in t.secteurs]
    return render_template('secteur/_manage_secteurs_form.html', texte=t, secteurs=secteurs, selected=selected)


@secteur.route('/admin/textes/<int:texte_id>/set_secteurs', methods=['POST'])
@login_required
@has_permission('secteur.gerer_textes')
def set_textes_secteurs(texte_id):
    """Set the list of secteurs for a texte. Expects form field 'secteur_ids' (multiple)"""
    t = TexteReglementaire.query.get_or_404(texte_id)
    # Accept both form-encoded and JSON
    if request.is_json:
        data = request.get_json() or {}
        ids = data.get('secteur_ids') or []
    else:
        ids = request.form.getlist('secteur_ids')

    # convert to ints and filter
    try:
        ids = [int(i) for i in ids if i is not None and str(i).strip() != '']
    except ValueError:
        return jsonify({'success': False, 'message': 'IDs invalid'}), 400

    # fetch secteurs and assign
    if ids:
        secteurs = Secteur.query.filter(Secteur.id.in_(ids)).all()
    else:
        secteurs = []

    t.secteurs = secteurs
    db.session.commit()

    return jsonify({'success': True, 'secteur_ids': [s.id for s in t.secteurs]})


@secteur.route('/create', methods=['GET', 'POST'])
@login_required
@has_permission('secteur.cree')
def create_secteur():
    """Create a new Secteur. Supports GET (form HTML) and POST (create).

    On success (POST) returns JSON { success: true, secteur: {...} }.
    On validation error returns the HTML form (partial) so the modal can display errors.
    """
    if request.method == 'GET':
        return render_template('secteur/_form.html', secteur=None, errors={})

    # POST
    nom = (request.form.get('nom') or '').strip()
    description = request.form.get('description')

    errors = {}
    if not nom:
        errors['nom'] = 'Le nom est requis.'
    elif Secteur.query.filter_by(nom=nom).first():
        errors['nom'] = 'Un secteur avec ce nom existe déjà.'

    if errors:
        return render_template('secteur/_form.html', secteur={'nom': nom, 'description': description}, errors=errors), 400

    s = Secteur(nom=nom, description=description)
    db.session.add(s)
    db.session.commit()

    return jsonify({'success': True, 'secteur': {'id': s.id, 'nom': s.nom, 'description': s.description}})


@secteur.route('/<int:secteur_id>/edit', methods=['GET', 'POST'])
@login_required
@has_permission('secteur.modifier')
def edit_secteur(secteur_id):
    """Edit an existing Secteur. GET returns partial form, POST updates and returns JSON."""
    s = Secteur.query.get_or_404(secteur_id)
    if request.method == 'GET':
        return render_template('secteur/_form.html', secteur=s, errors={})

    # POST
    nom = (request.form.get('nom') or '').strip()
    description = request.form.get('description')

    errors = {}
    if not nom:
        errors['nom'] = 'Le nom est requis.'
    else:
        other = Secteur.query.filter(Secteur.nom == nom, Secteur.id != s.id).first()
        if other:
            errors['nom'] = 'Un autre secteur avec ce nom existe déjà.'

    if errors:
        # re-render the form with errors and submitted data
        data = {'id': s.id, 'nom': nom, 'description': description}
        return render_template('secteur/_form.html', secteur=data, errors=errors), 400

    s.nom = nom
    s.description = description
    db.session.commit()

    return jsonify({'success': True, 'secteur': {'id': s.id, 'nom': s.nom, 'description': s.description}})

@secteur.route('/<int:secteur_id>/delete', methods=['POST'])
@login_required
@has_permission('secteur.modifier')
def delete_secteur(secteur_id):
    """Supprime un seul secteur."""
    s = Secteur.query.get_or_404(secteur_id)
    s.entreprises = []
    s.textes = []
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})

@secteur.route('/delete_all', methods=['POST'])
@login_required
@has_permission('secteur.modifier')
def delete_all_secteurs():
    """Supprime la totalité des secteurs."""
    secteurs = Secteur.query.all()
    for s in secteurs:
        s.entreprises = []
        s.textes = []
        db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})
