from flask import render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Entreprise, Secteur, TexteReglementaire, EntrepriseTexte, SubscriptionPlan, Utilisateur, Role
from app.entreprises import entreprises
from datetime import date, timedelta


@entreprises.route('/')
@login_required
def index():
    entreprises_list = Entreprise.query.all()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('entreprises/index.html', entreprises=entreprises_list, plans=plans)


@entreprises.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        taille = request.form.get('taille', 'PME')
        pays = request.form.get('pays', 'Maroc')
        adresse = request.form.get('adresse', '')
        contact_facturation_email = (request.form.get('contact_facturation_email') or '').strip() or None

        if not nom:
            flash('Le nom de l\'entreprise est requis.', 'warning')
            secteurs = Secteur.query.order_by(Secteur.nom).all()
            plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
            return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)

        mgr_nom = request.form.get('mgr_nom', '').strip()
        mgr_prenom = request.form.get('mgr_prenom', '').strip()
        mgr_email = request.form.get('mgr_email', '').strip()
        mgr_password = request.form.get('mgr_password', '')

        if not (mgr_nom and mgr_prenom and mgr_email and mgr_password):
            flash('Nom, prénom, email et mot de passe du manager sont requis.', 'warning')
            secteurs = Secteur.query.order_by(Secteur.nom).all()
            plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
            return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)

        if Utilisateur.query.filter_by(email=mgr_email).first():
            flash('Un utilisateur existe déjà avec cet email.', 'danger')
            secteurs = Secteur.query.order_by(Secteur.nom).all()
            plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
            return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)

        # 23 modules activables
        ALL_MODULES = [
            'pilotage', 'ged', 'veille', 'processus', 'audits', 'qualite',
            'nc_capa', 'formations', 'rh_qhse', 'haccp', 'hse', 'environnement',
            'maintenance', 'laboratoire', 'fournisseurs', 'performance',
            'planification', 'reunions', 'support', 'notifications',
            'admin', 'connaissances', 'urgences',
        ]
        modules = []
        for mod in ALL_MODULES:
            if request.form.get(f'module_{mod}'):
                modules.append(mod)

        selected_secteur_ids = request.form.getlist('secteurs')

        plan_key = (request.form.get('abonnement_type') or '').strip().lower() or None
        plan = SubscriptionPlan.query.filter_by(plan_key=plan_key).first() if plan_key else None
        default_trial = (plan.trial_days if plan else None) or 14
        trial_override = request.form.get('trial_days')
        try:
            trial_days = int(trial_override) if (trial_override or '').strip() else default_trial
        except (TypeError, ValueError):
            trial_days = default_trial

        entreprise = Entreprise(
            nom=nom,
            taille=taille,
            pays=pays,
            adresse=adresse,
            modules_actifs=modules,
            abonnement_type=plan_key or 'trial',
            statut='Actif',
            date_inscription=date.today(),
            contact_facturation_email=contact_facturation_email,
            periode_essai_jours=trial_days,
            date_debut_essai=None,
        )
        entreprise.abonnement_prochaine_echeance = date.today() + timedelta(days=trial_days)
        db.session.add(entreprise)
        db.session.flush()

        role_manager = Role.query.filter_by(nom='Manager', est_systeme=False).first()
        if not role_manager:
            role_manager = Role(nom='Manager', description='Manager d\'entreprise', est_systeme=False)
            db.session.add(role_manager)
            db.session.flush()

        admin = Utilisateur(
            nom=mgr_nom,
            prenom=mgr_prenom,
            email=mgr_email,
            entreprise_id=entreprise.id,
            role_id=role_manager.id,
            actif=True,
        )
        admin.set_password(mgr_password)
        db.session.add(admin)

        secteur_ids_int = [int(s) for s in selected_secteur_ids if s.isdigit()]
        auto_linked_count = 0
        if secteur_ids_int:
            secteurs = Secteur.query.filter(Secteur.id.in_(secteur_ids_int)).all()
            entreprise.secteurs.extend(secteurs)

            textes_cibles = (
                TexteReglementaire.query
                .join(TexteReglementaire.secteurs)
                .filter(
                    Secteur.id.in_(secteur_ids_int),
                    TexteReglementaire.version_active_id.isnot(None),
                )
                .distinct()
                .all()
            )

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
                        responsable_id=admin.id,
                        statut_obligation='OBLIGATOIRE',
                        motif_obligation='Réglementation sectorielle',
                        mode_evaluation='PERIMETRE_GLOBAL',
                    )
                )
                auto_linked_count += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Erreur création entreprise")
            flash('Erreur lors de la création de l\'entreprise.', 'danger')
            secteurs = Secteur.query.order_by(Secteur.nom).all()
            plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
            return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)

        flash(
            f'Entreprise créée avec succès. {auto_linked_count} texte(s) lié(s) automatiquement selon les secteurs.',
            'success',
        )
        return redirect(url_for('entreprises.index'))

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)


@entreprises.route('/<int:entreprise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(entreprise_id):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        flash('Entreprise introuvable.', 'danger')
        return redirect(url_for('entreprises.index'))
    if request.method == 'POST':
        entreprise.nom = request.form.get('nom', entreprise.nom)
        entreprise.taille = request.form.get('taille', entreprise.taille)
        entreprise.adresse = request.form.get('adresse', entreprise.adresse)
        entreprise.telephone = request.form.get('telephone', entreprise.telephone)
        entreprise.pays = request.form.get('pays', entreprise.pays)

        # 23 modules activables
        ALL_MODULES = [
            'pilotage', 'ged', 'veille', 'processus', 'audits', 'qualite',
            'nc_capa', 'formations', 'rh_qhse', 'haccp', 'hse', 'environnement',
            'maintenance', 'laboratoire', 'fournisseurs', 'performance',
            'planification', 'reunions', 'support', 'notifications',
            'admin', 'connaissances', 'urgences',
        ]
        modules = []
        for mod in ALL_MODULES:
            if request.form.get(f'module_{mod}'):
                modules.append(mod)
        entreprise.modules_actifs = modules

        if request.form.get('abonnement_type'):
            entreprise.abonnement_type = request.form.get('abonnement_type')
        db.session.commit()
        flash('Entreprise mise à jour.', 'success')
        return redirect(url_for('entreprises.index'))

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('entreprises/edit.html', entreprise=entreprise, secteurs=secteurs, plans=plans)


@entreprises.route('/api/liste')
@login_required
def api_liste():
    items = Entreprise.query.order_by(Entreprise.nom).all()
    return jsonify([{
        'id': r.id,
        'nom': r.nom,
        'taille': r.taille,
        'pays': r.pays,
        'modules_actifs': r.modules_actifs,
        'statut': r.statut,
        'abonnement_type': r.abonnement_type,
        'date_inscription': r.date_inscription.isoformat() if r.date_inscription else None,
        'nb_utilisateurs': len(r.utilisateurs) if hasattr(r, 'utilisateurs') else 0,
    } for r in items])


@entreprises.route('/api/<int:item_id>/detail')
@login_required
def api_detail(item_id):
    r = db.session.get(Entreprise, item_id)
    if not r:
        abort(404)
    plan = SubscriptionPlan.query.filter_by(plan_key=r.abonnement_type).first()
    return jsonify({
        'id': r.id,
        'nom': r.nom,
        'taille': r.taille,
        'pays': r.pays,
        'adresse': r.adresse,
        'telephone': r.telephone,
        'modules_actifs': r.modules_actifs,
        'statut': r.statut,
        'abonnement_type': r.abonnement_type,
        'plan_label': plan.label if plan else r.abonnement_type,
        'date_inscription': r.date_inscription.isoformat() if r.date_inscription else None,
        'nb_utilisateurs': len(r.utilisateurs) if hasattr(r, 'utilisateurs') else 0,
        'motif_suspension': r.motif_suspension,
        'abonnement_prochaine_echeance': r.abonnement_prochaine_echeance.isoformat() if r.abonnement_prochaine_echeance else None,
        'abonnement_paye': r.abonnement_paye,
    })


@entreprises.route('/api/<int:item_id>/update', methods=['POST'])
@login_required
def api_update(item_id):
    r = db.session.get(Entreprise, item_id)
    if not r:
        abort(404)
    data = request.get_json()
    for f in ('nom', 'taille', 'pays', 'adresse', 'telephone', 'statut',
              'abonnement_type', 'motif_suspension'):
        if f in data and data[f] is not None:
            setattr(r, f, data[f])
    if 'abonnement_prochaine_echeance' in data and data['abonnement_prochaine_echeance']:
        r.abonnement_prochaine_echeance = date.fromisoformat(data['abonnement_prochaine_echeance'])
    if 'abonnement_paye' in data:
        r.abonnement_paye = bool(data['abonnement_paye'])
    if 'modules_actifs' in data:
        r.modules_actifs = data['modules_actifs']
    db.session.commit()
    return jsonify({'success': True})


@entreprises.route('/api/<int:item_id>/delete', methods=['POST'])
@login_required
def api_delete(item_id):
    r = db.session.get(Entreprise, item_id)
    if not r:
        abort(404)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})
