from flask import render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from flask_login import current_user
from app import db
from app.models import Entreprise, Secteur, TexteReglementaire, EntrepriseTexte, SubscriptionPlan, Utilisateur, Role
from app.entreprises import entreprises
from app.utils.permissions import access_required
from datetime import date, timedelta


@entreprises.route('/')
@access_required()
def index():
    entreprises_list = Entreprise.query.all()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('entreprises/index.html', entreprises=entreprises_list, plans=plans)


@entreprises.route('/create', methods=['GET', 'POST'])
@access_required(permission='entreprises.cree')
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

        if not (mgr_nom and mgr_prenom and mgr_email):
            flash('Nom, prénom et email du manager sont requis.', 'warning')
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

        from app.utils.subscriptions import get_subscription_plan

        plan_key = (request.form.get('abonnement_type') or '').strip().lower() or None
        plan = get_subscription_plan(plan_key) if plan_key else None
        trial_override = request.form.get('trial_days')
        trial_days = 14
        if plan_key == 'trial':
            trial_days = int(trial_override) if (trial_override or '').strip() else 14

        entreprise = Entreprise(
            nom=nom,
            taille=taille,
            pays=pays,
            adresse=adresse,
            modules_actifs=modules,
            abonnement_type='essential' if plan_key == 'trial' else (plan_key or 'essential'),
            statut='trial',
            date_inscription=date.today(),
            contact_facturation_email=contact_facturation_email,
            periode_essai_jours=trial_days if plan_key == 'trial' else None,
            date_debut_essai=date.today() if plan_key == 'trial' else None,
        )
        if plan_key == 'trial':
            entreprise.abonnement_prochaine_echeance = date.today() + timedelta(days=trial_days)
        else:
            entreprise.abonnement_prochaine_echeance = date.today() + timedelta(days=14)
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
        db.session.add(admin)

        # Copier les permissions globales des rôles vers cette entreprise
        from app.models import Permission, RolePermission
        from app.utils.permission_catalog import get_default_enterprise_role_permissions
        default_perms = get_default_enterprise_role_permissions()
        for role_nom in ['Manager', 'Auditeur', 'Responsable operationnel', 'Consultant']:
            role = Role.query.filter_by(nom=role_nom).first()
            if not role:
                continue
            perms_to_add = default_perms.get(role_nom, ())
            for code in perms_to_add:
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    continue
                if not RolePermission.query.filter_by(
                    role_id=role.id, permission_id=perm.id, entreprise_id=entreprise.id
                ).first():
                    db.session.add(RolePermission(
                        role_id=role.id, permission_id=perm.id,
                        entreprise_id=entreprise.id, autorise=True
                    ))

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

        # Envoyer un email de bienvenue au manager
        from app.utils.notifications import send_account_created_email
        token = admin.get_reset_token()
        activation_link = url_for('users.reset_password_token', token=token, _external=True)
        login_url = current_app.config.get('APP_LOGIN_URL', 'http://localhost:5006/')
        email_sent = send_account_created_email(
            recipient_email=admin.email,
            recipient_name=f"{admin.prenom} {admin.nom}",
            role_name=role_manager.nom if role_manager else None,
            login_link=login_url,
            activation_link=activation_link,
        )
        if email_sent:
            current_app.logger.info("Email bienvenue envoyé avec succès à %s", admin.email)
        else:
            current_app.logger.error("Erreur envoi email bienvenue à %s", admin.email)

        flash(
            f'Entreprise créée avec succès. {auto_linked_count} texte(s) lié(s) automatiquement selon les secteurs. '
            f'Un email de bienvenue a été envoyé à {admin.email}.',
            'success',
        )
        return redirect(url_for('entreprises.index'))

    secteurs = Secteur.query.order_by(Secteur.nom).all()
    plans = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('entreprises/create.html', secteurs=secteurs, plans=plans)


@entreprises.route('/<int:entreprise_id>/edit', methods=['GET', 'POST'])
@access_required()
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
        db.session.commit()
        flash('Entreprise mise à jour.', 'success')
        return redirect(url_for('entreprises.index'))

    manager = Utilisateur.query.filter_by(entreprise_id=entreprise_id).order_by(Utilisateur.date_creation).first()
    return render_template('entreprises/edit.html', entreprise=entreprise, manager=manager)


@entreprises.route('/<int:entreprise_id>/resend-welcome-email', methods=['POST'])
@access_required(permission='entreprises.modifier')
def resend_welcome_email(entreprise_id):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        flash('Entreprise introuvable.', 'danger')
        return redirect(url_for('entreprises.index'))

    admin = Utilisateur.query.filter_by(entreprise_id=entreprise.id).order_by(Utilisateur.date_creation).first()
    if not admin:
        flash('Aucun utilisateur trouvé pour cette entreprise.', 'warning')
        dest = request.form.get('redirect_url') or url_for('entreprises.edit', entreprise_id=entreprise_id)
        return redirect(dest)

    from app.utils.notifications import send_account_created_email
    token = admin.get_reset_token()
    activation_link = url_for('users.reset_password_token', token=token, _external=True)
    success = send_account_created_email(
        recipient_email=admin.email,
        recipient_name=f"{admin.prenom} {admin.nom}",
        role_name=admin.role.nom if admin.role else None,
        login_link=current_app.config.get('APP_LOGIN_URL', 'http://localhost:5006/'),
        activation_link=activation_link,
    )
    if success:
        flash(f'Email de bienvenue renvoyé à {admin.email}.', 'success')
    else:
        flash("Erreur lors de l'envoi de l'email. Vérifiez la configuration du serveur mail.", 'danger')

    dest = request.form.get('redirect_url') or url_for('entreprises.edit', entreprise_id=entreprise_id)
    return redirect(dest)


@entreprises.route('/api/liste')
@access_required()
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
@access_required()
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
@access_required(permission='entreprises.modifier')
def api_update(item_id):
    r = db.session.get(Entreprise, item_id)
    if not r:
        abort(404)
    data = request.get_json()
    for f in ('nom', 'taille', 'pays', 'adresse', 'telephone'):
        if f in data and data[f] is not None:
            setattr(r, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@entreprises.route('/api/<int:item_id>/delete', methods=['POST'])
@access_required(permission='entreprises.supprimer')
def api_delete(item_id):
    r = db.session.get(Entreprise, item_id)
    if not r:
        abort(404)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})
@entreprises.route('/mon-entreprise')
@access_required(permission='entreprises.modifier')
def management():
    """
    Console de management locale pour les administrateurs d'entreprise.
    Permet de gérer les informations de la société, voir les modules actifs
    et superviser l'équipe sans avoir accès à l'administration globale.
    """
    from app.models import SubscriptionPlan, ActionCorrective
    from app.utils.subscriptions import get_subscription_plan

    entreprise_id = current_user.entreprise_id
    if not entreprise_id:
        abort(403)
        
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        abort(404)
    
    # Statistiques de l'équipe
    users_count = Utilisateur.query.filter_by(entreprise_id=entreprise.id).count()
    users_actifs = Utilisateur.query.filter_by(entreprise_id=entreprise.id, actif=True).count()

    # Quotas du plan d'abonnement
    plan = get_subscription_plan(entreprise.abonnement_type)
    max_users = plan.get('max_users') if plan else None
    max_documents = plan.get('max_documents') if plan else None
    max_actions = plan.get('max_open_actions') if plan else None
    max_storage_mb = plan.get('max_storage_mb') if plan else None
    
    # Usage
    open_actions = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == entreprise.id,
        ActionCorrective.statut.in_(['ouverte', 'en_cours'])
    ).count() if max_actions else None

    from app.models.proofs import ProofMaster
    proof_masters = ProofMaster.query.filter_by(entreprise_id=entreprise.id).all()
    used_documents = len({pm.nom_fichier for pm in proof_masters}) if max_documents else None
    used_storage_bytes = sum(pm.taille_bytes or 0 for pm in proof_masters)
    used_storage_mb = round(used_storage_bytes / (1024 * 1024), 1) if max_storage_mb else None
    
    # Modules
    from app.core import plugin_manager
    active_manifests = plugin_manager.get_active_modules(entreprise.id)
    all_manifests = plugin_manager.get_all_manifests()
    
    return render_template(
        'entreprises/management.html',
        entreprise=entreprise,
        users_count=users_count,
        users_actifs=users_actifs,
        active_manifests=active_manifests,
        all_manifests=[m for m in all_manifests if m.visible],
        plan=plan,
        max_users=max_users,
        max_actions=max_actions,
        max_documents=max_documents,
        max_storage_mb=max_storage_mb,
        open_actions=open_actions,
        used_documents=used_documents,
        used_storage_mb=used_storage_mb,
    )
