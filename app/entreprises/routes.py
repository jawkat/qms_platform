from flask import render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise, Secteur, TexteReglementaire, EntrepriseTexte
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

        selected_secteur_ids = request.form.getlist('secteurs')

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
        db.session.flush()

        if selected_secteur_ids:
            secteurs = Secteur.query.filter(Secteur.id.in_([int(s) for s in selected_secteur_ids if s])).all()
            entreprise.secteurs.extend(secteurs)

            textes_cibles = (
                TexteReglementaire.query
                .join(TexteReglementaire.secteurs)
                .filter(
                    Secteur.id.in_([int(s) for s in selected_secteur_ids if s]),
                    TexteReglementaire.version_active_id.isnot(None),
                )
                .distinct()
                .all()
            )

            auto_linked_count = 0
            for texte in textes_cibles:
                version_id = texte.version_active_id
                if not version_id:
                    continue

                already_linked = EntrepriseTexte.query.filter_by(
                    entreprise_id=entreprise.id,
                    texte_version_id=version_id,
                ).first()
                if already_linked:
                    continue

                db.session.add(
                    EntrepriseTexte(
                        entreprise_id=entreprise.id,
                        texte_version_id=version_id,
                        statut_obligation='OBLIGATOIRE',
                        motif_obligation='Réglementation sectorielle',
                        mode_evaluation='PERIMETRE_GLOBAL',
                    )
                )
                auto_linked_count += 1

            db.session.commit()
            flash(
                f'Entreprise créée avec succès. {auto_linked_count} texte(s) lié(s) automatiquement selon les secteurs.',
                'success',
            )
        else:
            db.session.commit()
            flash('Entreprise créée avec succès.', 'success')

        return redirect(url_for('entreprises.index'))

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('entreprises/create.html', secteurs=secteurs)


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

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('entreprises/edit.html', entreprise=entreprise, secteurs=secteurs)
