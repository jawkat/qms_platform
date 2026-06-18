import os
from datetime import date, datetime, timedelta

from flask import current_app
from app import db
from app.models import ActionCorrective, Entreprise, Utilisateur, ProofMaster
from app.utils.subscriptions import (
    get_subscription_plan,
    get_subscription_quota_limit,
    get_subscription_user_limit,
)


BLOCKED_LIFECYCLE_STATES = {'suspended', 'cancelled', 'archived'}


def _document_storage_key(doc):
    chemin = (getattr(doc, 'chemin', None) or '').strip()
    if chemin:
        return ('chemin', chemin)
    return ('id', getattr(doc, 'id', None))


def _get_storage_size_for_documents(documents):
    upload_root = current_app.config.get('UPLOAD_FOLDER')
    if not upload_root:
        return 0

    total = 0
    seen_paths = set()
    for doc in documents:
        if not doc.chemin:
            continue
        if doc.chemin in seen_paths:
            continue
        seen_paths.add(doc.chemin)
        full_path = os.path.join(upload_root, doc.chemin)
        try:
            if os.path.exists(full_path):
                total += os.path.getsize(full_path)
        except OSError:
            # Ignore missing/inaccessible files for quota computation.
            continue
    return total


def get_enterprise_lifecycle_status(entreprise):
    raw_status = (getattr(entreprise, 'statut', None) or '').strip().lower()
    if raw_status in {'trial', 'active', 'suspended', 'cancelled', 'archived'}:
        return raw_status

    if getattr(entreprise, 'abonnement_paye', False):
        return 'active'

    # Legacy-safe default: tenants without explicit lifecycle remain active.
    return 'active'


def ensure_enterprise_operation_allowed(entreprise, operation_label):
    lifecycle = get_enterprise_lifecycle_status(entreprise)
    if lifecycle in BLOCKED_LIFECYCLE_STATES:
        message = (
            f"Operation indisponible ({operation_label}): "
            f"cycle client '{lifecycle}'."
        )
        return False, message, lifecycle
    return True, None, lifecycle


def get_user_limit_status(entreprise_id, extra_users=1):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        return False, None, None, None

    plan_key = getattr(entreprise, 'abonnement_type', None)
    limit = get_subscription_user_limit(plan_key)
    if not limit:
        return False, None, None, None

    current_count = Utilisateur.query.filter_by(entreprise_id=entreprise_id).count()
    reached = (current_count + extra_users) > limit
    plan = get_subscription_plan(plan_key)
    return reached, current_count, limit, (plan['label'] if plan else plan_key)


def get_action_limit_status(entreprise_id, extra_actions=1):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        return False, None, None, None

    plan_key = getattr(entreprise, 'abonnement_type', None)
    limit = get_subscription_quota_limit(plan_key, 'max_open_actions')
    if not limit:
        return False, None, None, None

    current_count = (
        ActionCorrective.query
        .filter(ActionCorrective.entreprise_id == entreprise_id, ActionCorrective.statut != 'Terminée')
        .count()
    )
    reached = (current_count + extra_actions) > limit
    plan = get_subscription_plan(plan_key)
    return reached, current_count, limit, (plan['label'] if plan else plan_key)


def get_documents_limit_status(entreprise_id, extra_documents=1):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        return False, None, None, None

    plan_key = getattr(entreprise, 'abonnement_type', None)
    limit = get_subscription_quota_limit(plan_key, 'max_documents')
    if not limit:
        return False, None, None, None

    proof_masters = (
        ProofMaster.query
        .filter(ProofMaster.entreprise_id == entreprise_id)
        .all()
    )

    current_count = len({_document_storage_key(pm) for pm in proof_masters})
    reached = (current_count + extra_documents) > limit
    plan = get_subscription_plan(plan_key)
    return reached, current_count, limit, (plan['label'] if plan else plan_key)


def get_storage_limit_status(entreprise_id, extra_bytes=0):
    entreprise = db.session.get(Entreprise, entreprise_id)
    if not entreprise:
        return False, None, None, None

    plan_key = getattr(entreprise, 'abonnement_type', None)
    limit_mb = get_subscription_quota_limit(plan_key, 'max_storage_mb')
    if not limit_mb:
        return False, None, None, None

    proof_masters = ProofMaster.query.filter(ProofMaster.entreprise_id == entreprise_id).all()
    current_bytes = _get_storage_size_for_documents(proof_masters)
    limit_bytes = int(limit_mb * 1024 * 1024)
    reached = (current_bytes + int(extra_bytes or 0)) > limit_bytes
    plan = get_subscription_plan(plan_key)
    return reached, current_bytes, limit_bytes, (plan['label'] if plan else plan_key)


def parse_optional_date(raw_value, field_label):
    value = (raw_value or '').strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValueError(f"Format de date invalide pour '{field_label}'.") from exc


def add_one_year_safe(d):
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + 1)


def get_payment_status(entreprise, today=None):
    """
    Calcule le vrai statut de paiement basé sur la date d'échéance.
    
    Returns: 'paid' (payé, même si renouvellement dû), 'expired' (dépassé ET non-payé), 'unpaid' (pas payé)
    """
    if today is None:
        today = date.today()
    
    due_date = getattr(entreprise, 'abonnement_prochaine_echeance', None)
    abonnement_paye = getattr(entreprise, 'abonnement_paye', False)
    
    # Si pas de date d'échéance, considérer comme non-payé
    if not due_date:
        return 'unpaid'
    
    # Si payé = payé (peu importe si date en passé, c'est un renouvellement dû, pas un impayé)
    if abonnement_paye:
        return 'paid'
    
    # Si date dépassée ET non-payé = expiré (c'est un véritable impayé)
    if due_date < today:
        return 'expired'
    
    # Sinon = pas encore payé
    return 'unpaid'


def get_enterprise_quota_info(entreprise, used_users):
    plan = get_subscription_plan(getattr(entreprise, 'abonnement_type', None))
    if not plan:
        return None

    max_users = plan['max_users']
    remaining_users = max(max_users - used_users, 0)
    usage_pct = int((used_users / max_users) * 100) if max_users else 0

    if remaining_users == 0:
        status = 'reached'
    elif usage_pct >= 80:
        status = 'warning'
    else:
        status = 'ok'

    return {
        'plan_label': plan['label'],
        'max_users': max_users,
        'used_users': used_users,
        'remaining_users': remaining_users,
        'usage_pct': usage_pct,
        'status': status,
        'max_documents': plan.get('max_documents'),
        'max_open_actions': plan.get('max_open_actions'),
        'max_storage_mb': plan.get('max_storage_mb'),
    }


def apply_subscription_update(entreprise, payload):
    abonnement_type = (payload.get('abonnement_type') or '').strip().lower()
    if abonnement_type and not get_subscription_plan(abonnement_type):
        raise ValueError("Type d'abonnement invalide.")

    entreprise.abonnement_type = abonnement_type or None
    entreprise.date_inscription = parse_optional_date(payload.get('date_inscription'), 'date 1ère inscription')
    typed_due_date = parse_optional_date(payload.get('abonnement_prochaine_echeance'), 'prochaine échéance')
    entreprise.abonnement_prochaine_echeance = typed_due_date
    force_due_date = payload.get('force_due_date') == '1'
    entreprise.abonnement_paye = payload.get('abonnement_paye') == '1'
    statut = (payload.get('statut') or '').strip().lower()
    if statut:
        if statut not in {'trial', 'active', 'suspended', 'cancelled', 'archived'}:
            raise ValueError("Statut de cycle de vie invalide.")
        entreprise.statut = statut
    elif not entreprise.statut:
        entreprise.statut = 'active'

    # If admin marks the entreprise as paid in the generic update form, do NOT
    # auto-extend the due date here. Auto-extension (+1 year) must only happen
    # when an actual payment is recorded via the dedicated payment endpoint
    # (`mark_abonnement_paid`). Here we only accept an explicit due date when
    # `force_due_date` is used or when an explicit `abonnement_prochaine_echeance`
    # is provided; otherwise leave the existing due date untouched.
    if entreprise.abonnement_paye:
        if force_due_date and typed_due_date:
            entreprise.abonnement_prochaine_echeance = typed_due_date
        elif typed_due_date:
            # Admin provided a specific next-due date — accept it without auto-rolling.
            entreprise.abonnement_prochaine_echeance = typed_due_date
        # Do not auto-add one year here; payments should be recorded via /abonnement/pay
        # Respect an explicit trial selection from the admin form. Only auto-promote
        # when no lifecycle status has been chosen.
        if entreprise.statut in {None, ''}:
            entreprise.statut = 'active'

    # Traiter les nouveaux champs de facturation
    montant_str = (payload.get('montant_annuel_mad') or '').strip()
    if montant_str:
        try:
            entreprise.montant_annuel_mad = int(montant_str)
        except ValueError:
            raise ValueError("Montant annuel doit être un nombre entier.")
    
    contact_email = (payload.get('contact_facturation_email') or '').strip()
    if contact_email:
        if '@' not in contact_email:
            raise ValueError("Email de facturation invalide.")
        entreprise.contact_facturation_email = contact_email
    
    motif = (payload.get('motif_suspension') or '').strip()
    if motif:
        valid_motifs = {'non_paye', 'demande_client', 'autre'}
        if motif not in valid_motifs:
            raise ValueError("Motif de suspension invalide.")
        entreprise.motif_suspension = motif
    else:
        entreprise.motif_suspension = None
    
    notes = (payload.get('notes_facturation') or '').strip()
    entreprise.notes_facturation = notes or None
    
    # Gérer marquer comme non-payé manuellement
    if payload.get('marquer_non_paye') == '1':
        entreprise.abonnement_paye = False
        # Optionnel: remettre la date au passé pour bien signaler l'expiration
        entreprise.abonnement_prochaine_echeance = date.today() - timedelta(days=1)
        if entreprise.statut in {'active', 'trial'} and not entreprise.motif_suspension:
            entreprise.statut = 'suspended'
            entreprise.motif_suspension = 'non_paye'

    db.session.add(entreprise)
    return entreprise
