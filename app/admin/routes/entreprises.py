from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import (
    Utilisateur, Entreprise, SubscriptionPlan, Secteur,
    TexteReglementaire, EntrepriseTexte, ActionCorrective, ProofMaster,
    HistoriquePaiement,
)
from app.services.subscription_service import (
    get_enterprise_lifecycle_status, get_payment_status,
    _get_storage_size_for_proofs, add_one_year_safe,
)
from app.utils.subscriptions import get_subscription_plan
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
    today = date.today()
    for e in entreprises:
        nb_users = Utilisateur.query.filter_by(entreprise_id=e.id).count()
        plan = SubscriptionPlan.query.filter_by(plan_key=e.abonnement_type).first()
        plan_def = get_subscription_plan(e.abonnement_type)
        lifecycle = get_enterprise_lifecycle_status(e)
        pay_status = get_payment_status(e)
        nb_actions = ActionCorrective.query.filter(
            ActionCorrective.entreprise_id == e.id,
            ActionCorrective.statut != 'Terminée',
        ).count()
        max_users = plan_def['max_users'] if plan_def else 0
        max_actions = plan_def['max_open_actions'] if plan_def else 0
        user_pct = int((nb_users / max_users) * 100) if max_users else 0
        action_pct = int((nb_actions / max_actions) * 100) if max_actions else 0
        due = getattr(e, 'abonnement_prochaine_echeance', None)
        days_remaining = (due - today).days if due else None
        data.append({
            'entreprise': e,
            'nb_users': nb_users,
            'plan_obj': plan,
            'lifecycle': lifecycle,
            'pay_status': pay_status,
            'nb_actions': nb_actions,
            'max_users': max_users,
            'max_actions': max_actions,
            'user_pct': user_pct,
            'action_pct': action_pct,
            'days_remaining': days_remaining,
        })
    return render_template('admin/entreprises.html', data=data, today=today)


@admin.route('/entreprises/create')
@login_required
@admin_required
def entreprise_create():
    return redirect(url_for('entreprises.create'))


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
                           utilisateurs=utilisateurs, plan=plan, plans=plans,
                           today=date.today().isoformat())


@admin.route('/entreprises/<int:eid>/update', methods=['POST'])
@login_required
@admin_required
def entreprise_update(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    for f in ('nom', 'taille', 'pays', 'adresse', 'telephone'):
        val = request.form.get(f)
        if val is not None:
            setattr(entreprise, f, val)
    abonnement_type = request.form.get('abonnement_type')
    modules_actifs = [m for m in request.form.getlist('modules_actifs') if m]
    statut = request.form.get('statut')
    motif_suspension = request.form.get('motif_suspension', '').strip()
    abonnement_paye = request.form.get('abonnement_paye')
    marquer_non_paye = request.form.get('marquer_non_paye')
    if abonnement_type:
        entreprise.abonnement_type = abonnement_type
    if modules_actifs is not None and request.form.get('modules_submitted'):
        entreprise.modules_actifs = modules_actifs
    if abonnement_paye:
        entreprise.abonnement_paye = True
        # Étendre l'échéance d'1 an si elle est passée ou absente
        due = entreprise.abonnement_prochaine_echeance
        today = date.today()
        if not due or due < today:
            entreprise.abonnement_prochaine_echeance = add_one_year_safe(today)
        entreprise.date_dernier_paiement = today
        entreprise.statut = 'active'
        entreprise.motif_suspension = None
    if marquer_non_paye:
        entreprise.abonnement_paye = False
        if not statut:
            entreprise.statut = 'suspended'
            entreprise.motif_suspension = entreprise.motif_suspension or 'Impayé'
    if statut:
        normalize = {'actif': 'active', 'suspendu': 'suspended',
                     'en_attente': 'suspended', 'annule': 'cancelled',
                     'archive': 'archived'}
        entreprise.statut = normalize.get(statut.lower(), statut)
    if motif_suspension:
        entreprise.motif_suspension = motif_suspension
    else:
        entreprise.motif_suspension = None
    db.session.commit()
    flash('Entreprise mise à jour avec succès.', 'success')
    tab = request.form.get('active_tab', '')
    fragment = f'#{tab}' if tab else ''
    return redirect(url_for('admin.entreprise_detail', eid=eid) + fragment)


@admin.route('/entreprises/<int:eid>/api/quota')
@login_required
@admin_required
def entreprise_api_quota(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    from app.models import ActionCorrective, ProofMaster
    plan = SubscriptionPlan.query.filter_by(plan_key=entreprise.abonnement_type).first()
    nb_users = Utilisateur.query.filter_by(entreprise_id=eid).count()
    nb_actions = ActionCorrective.query.filter(
        ActionCorrective.entreprise_id == eid,
        ActionCorrective.statut != 'Terminée',
    ).count()
    nb_docs = ProofMaster.query.filter_by(entreprise_id=eid, statut='ACTIF').count()
    proofs = ProofMaster.query.filter_by(entreprise_id=eid, statut='ACTIF').all()
    storage = _get_storage_size_for_proofs(proofs)
    return jsonify({
        'used_users': nb_users,
        'max_users': plan.max_users if plan else 0,
        'used_actions': nb_actions,
        'max_actions': plan.max_open_actions if plan else 0,
        'used_documents': nb_docs,
        'max_documents': plan.max_documents if plan else 0,
        'used_storage_mb': round(storage, 1) if storage else 0,
        'max_storage_mb': plan.max_storage_mb if plan else 0,
    })


@admin.route('/entreprises/<int:eid>/api/paiements')
@login_required
@admin_required
def entreprise_api_paiements(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    items = HistoriquePaiement.query.filter_by(entreprise_id=eid)\
        .order_by(HistoriquePaiement.date_paiement.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_paiement': r.date_paiement.isoformat() if r.date_paiement else None,
        'montant_mad': float(r.montant_mad) if r.montant_mad else None,
        'methode_paiement': r.methode_paiement,
        'reference_externe': r.reference_externe,
        'statut_paiement': r.statut_paiement,
        'notes': r.notes,
        'enregistre_par': r.enregistre_par,
    } for r in items])


@admin.route('/entreprises/<int:eid>/api/paiements/create', methods=['POST'])
@login_required
@admin_required
def entreprise_api_paiements_create(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Données requises.'}), 400
    try:
        date_paiement = datetime.strptime(data['date_paiement'], '%Y-%m-%d').date() if data.get('date_paiement') else date.today()
        montant = float(data.get('montant_mad', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Montant ou date invalide.'}), 400

    paiement = HistoriquePaiement(
        entreprise_id=eid,
        date_paiement=date_paiement,
        montant_mad=montant,
        methode_paiement=data.get('methode_paiement'),
        reference_externe=data.get('reference_externe'),
        statut_paiement='valide',
        notes=data.get('notes'),
        enregistre_par=current_user.id,
    )
    db.session.add(paiement)

    # Étendre l'échéance d'1 an à partir de la date d'échéance actuelle (ou de la date de paiement si pas d'échéance)
    due = entreprise.abonnement_prochaine_echeance
    if due and due >= date.today():
        entreprise.abonnement_prochaine_echeance = add_one_year_safe(due)
    else:
        entreprise.abonnement_prochaine_echeance = add_one_year_safe(date_paiement)

    entreprise.abonnement_paye = True
    entreprise.date_dernier_paiement = date_paiement
    entreprise.montant_annuel_mad = montant
    entreprise.statut = 'active'
    entreprise.motif_suspension = None

    db.session.commit()
    return jsonify({'success': True, 'id': paiement.id})


@admin.route('/entreprises/<int:eid>/suspendre', methods=['POST'])
@login_required
@admin_required
def entreprise_suspendre(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    s = (entreprise.statut or '').lower()
    if s in ('actif', 'active', 'trial'):
        entreprise.statut = 'suspended'
        entreprise.motif_suspension = request.form.get('motif', 'Suspendu par administrateur')
    else:
        entreprise.statut = 'active'
        entreprise.motif_suspension = None
    db.session.commit()
    flash(f'Entreprise {entreprise.nom} {"suspendue" if entreprise.statut == "suspended" else "réactivée"}.', 'success')
    dest = request.form.get('redirect_url') or url_for('admin.entreprises')
    return redirect(dest)
