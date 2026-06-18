from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise
from app.entreprises import entreprises
from datetime import date


@entreprises.route('/')
@login_required
def index():
    entreprises_list = Entreprise.query.all()
    return render_template('entreprises/index.html', entreprises=entreprises_list)


@entreprises.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        modules = ['hse']
        if request.form.get('module_qualite'):
            modules.append('qualite')
        entreprise = Entreprise(
            nom=request.form['nom'],
            taille=request.form.get('taille', 'PME'),
            pays=request.form.get('pays', 'Maroc'),
            adresse=request.form.get('adresse'),
            modules_actifs=modules,
            statut='Actif',
            date_inscription=date.today(),
        )
        db.session.add(entreprise)
        db.session.commit()
        flash('Entreprise creee avec succes.', 'success')
        return redirect(url_for('entreprises.index'))
    return render_template('entreprises/create.html')


@entreprises.route('/<int:entreprise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(entreprise_id):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if request.method == 'POST':
        entreprise.nom = request.form.get('nom', entreprise.nom)
        entreprise.taille = request.form.get('taille', entreprise.taille)
        entreprise.adresse = request.form.get('adresse', entreprise.adresse)
        modules = ['hse']
        if request.form.get('module_qualite'):
            modules.append('qualite')
        entreprise.modules_actifs = modules
        db.session.commit()
        flash('Entreprise mise a jour.', 'success')
        return redirect(url_for('entreprises.index'))
    return render_template('entreprises/edit.html', entreprise=entreprise)
