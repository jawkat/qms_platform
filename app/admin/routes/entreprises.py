from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import (
    Utilisateur, Entreprise, SubscriptionPlan, Secteur,
    TexteReglementaire, EntrepriseTexte
)
from functools import wraps
from datetime import date, datetime, time, timedelta


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.role or not current_user.role.est_systeme:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route('/')
@login_required
@admin_required
def dashboard():
    from app.models import ActionCorrective, ProofMaster, JournalSecurite
    stats = {
        'entreprises': Entreprise.query.count(),
        'utilisateurs': Utilisateur.query.count(),
        'actions_en_cours': ActionCorrective.query.filter(
            ActionCorrective.statut.in_(['A_FAIRE', 'EN_COURS'])
        ).count(),
        'documents_actifs': ProofMaster.query.filter_by(statut='ACTIF').count(),
    }
    logs = JournalSecurite.query.order_by(JournalSecurite.date_action.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, logs=logs)


@admin.route('/entreprises')
@login_required
@admin_required
def entreprises():
    entreprises = Entreprise.query.order_by(Entreprise.date_inscription.desc()).all()
    data = []
    for e in entreprises:
        nb_users = Utilisateur.query.filter_by(entreprise_id=e.id).count()
        plan = SubscriptionPlan.query.filter_by(plan_key=e.abonnement_type).first()
        data.append({'entreprise': e, 'nb_users': nb_users, 'plan': plan})
    return render_template('admin/entreprises.html', data=data)


@admin.route('/entreprises/create', methods=['GET', 'POST'])
@login_required
@admin_required
def entreprise_create():
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
                        motif_obligation='Reglementation sectorielle',
                        mode_evaluation='PERIMETRE_GLOBAL',
                    )
                )
                auto_linked_count += 1
            db.session.commit()
            flash(
                f'Entreprise creee avec succes. {auto_linked_count} texte(s) lie(s) automatiquement selon les secteurs.',
                'success',
            )
        else:
            db.session.commit()
            flash('Entreprise creee avec succes.', 'success')
        return redirect(url_for('admin.entreprises'))
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template('admin/entreprise_create.html', secteurs=secteurs)


@admin.route('/entreprises/<int:eid>')
@login_required
@admin_required
def entreprise_detail(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    utilisateurs = Utilisateur.query.filter_by(entreprise_id=eid).all()
    plan = SubscriptionPlan.query.filter_by(plan_key=entreprise.abonnement_type).first()
    plans = SubscriptionPlan.query.all()
    return render_template('admin/entreprise_detail.html', entreprise=entreprise,
                           utilisateurs=utilisateurs, plan=plan, plans=plans)


@admin.route('/entreprises/<int:eid>/update', methods=['POST'])
@login_required
@admin_required
def entreprise_update(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    abonnement_type = request.form.get('abonnement_type')
    modules_actifs = request.form.getlist('modules_actifs')
    statut = request.form.get('statut')
    motif_suspension = request.form.get('motif_suspension', '').strip()
    if abonnement_type:
        entreprise.abonnement_type = abonnement_type
    if modules_actifs:
        entreprise.modules_actifs = modules_actifs
    if statut:
        entreprise.statut = statut
    if motif_suspension:
        entreprise.motif_suspension = motif_suspension
    else:
        entreprise.motif_suspension = None
    db.session.commit()
    flash('Entreprise mise à jour avec succès.', 'success')
    return redirect(url_for('admin.entreprise_detail', eid=eid))


@admin.route('/entreprises/<int:eid>/suspendre', methods=['POST'])
@login_required
@admin_required
def entreprise_suspendre(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    if entreprise.statut == 'Actif':
        entreprise.statut = 'Suspendu'
        entreprise.motif_suspension = request.form.get('motif', 'Suspendu par administrateur')
    else:
        entreprise.statut = 'Actif'
        entreprise.motif_suspension = None
    db.session.commit()
    flash(f'Entreprise {entreprise.nom} {"suspendue" if entreprise.statut == "Suspendu" else "réactivée"}.', 'success')
    return redirect(url_for('admin.entreprises'))
