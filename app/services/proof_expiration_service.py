from datetime import date, timedelta, datetime
import logging

from app import db
from app.models import Notification, TacheSysteme, ProofMaster
from app.utils.notifications import create_notification


DEFAULT_EXPIRATION_REMINDER_DAYS = 30
logger = logging.getLogger(__name__)


def _build_marker(proof_id, due_date, kind):
    """Créer un marqueur pour une preuve (basé sur ProofMaster)"""
    return f"[PROOF:{proof_id}][DUE:{due_date.isoformat()}][TYPE:{kind}]"


def _notification_exists(user_id, marker):
    """Vérifier si notification existe déjà (éviter doublon)"""
    return (
        Notification.query
        .filter(
            Notification.utilisateur_id == user_id,
            Notification.message.contains(marker),
        )
        .first()
        is not None
    )


def run_daily_proof_expiration_reminders(reminder_days=DEFAULT_EXPIRATION_REMINDER_DAYS, today=None):
    """
    Grouper par ProofMaster pour éviter les notifications dupliquées
    quand une preuve est attachée à plusieurs évaluations.
    
    Returns:
        Dict avec statistiques de traitement
    """
    today = today or date.today()
    horizon = today + timedelta(days=reminder_days)

    logger.info(
        "proof_reminder_job_started reminder_days=%s date=%s",
        reminder_days,
        today.isoformat(),
        extra={'request_id': 'job-proof-reminder', 'tenant_id': '-', 'user_id': '-'},
    )

    stats = {
        'processed_proofs': 0,
        'processed_documents': 0,
        'soon_notifications': 0,
        'expired_notifications': 0,
        'errors': 0,
    }

    # Requête par ProofMaster
    proofs = (
        ProofMaster.query
        .filter(
            ProofMaster.validite.isnot(None),
            ProofMaster.statut == 'ACTIF'  # Ignorer les remplacées/supprimées
        )
        .all()
    )

    for proof in proofs:
        stats['processed_proofs'] += 1
        stats['processed_documents'] += 1
        
        # Récupérer l'ensemble des users liés par ProofReferences
        recipients = proof.get_recipients()
        
        try:
            if proof.validite < today:
                # Preuve EXPIRÉE
                marker = _build_marker(proof.id, proof.validite, 'EXPIRED')
                for user_id in recipients:
                    if _notification_exists(user_id, marker):
                        continue
                    create_notification(
                        user_id,
                        (
                            f"Preuve EXPIRÉE: '{proof.nom_fichier}' est expirée depuis le "
                            f"{proof.validite.strftime('%d/%m/%Y')} [PROOF:{proof.id}][TYPE:EXPIRED]"
                        ),
                        type='danger',
                    )
                    stats['expired_notifications'] += 1
            
            elif today <= proof.validite <= horizon:
                # Preuve EXPIRATION PROCHE
                days_left = (proof.validite - today).days
                marker = _build_marker(proof.id, proof.validite, 'REMINDER')
                for user_id in recipients:
                    if _notification_exists(user_id, marker):
                        continue
                    create_notification(
                        user_id,
                        (
                            f"Rappel PREUVE: '{proof.nom_fichier}' expire dans {days_left} jour(s) le "
                            f"{proof.validite.strftime('%d/%m/%Y')} [PROOF:{proof.id}][TYPE:REMINDER]"
                        ),
                        type='warning',
                    )
                    stats['soon_notifications'] += 1
        
        except Exception:
            logger.exception(f"Erreur traitement preuve {proof.id}")
            stats['errors'] += 1

    # Enregistrer résultat de la tâche
    task = TacheSysteme(
        type_tache='proof_expiration_reminders',
        date_execution=datetime.utcnow(),
        statut='success' if stats['errors'] == 0 else 'partial_success',
        resultat=(
            f"processed={stats['processed_proofs']};"
            f"soon={stats['soon_notifications']};"
            f"expired={stats['expired_notifications']};"
            f"errors={stats['errors']}"
        ),
    )
    db.session.add(task)
    db.session.commit()

    logger.info(
        "proof_reminder_job_finished processed=%s soon=%s expired=%s errors=%s",
        stats['processed_proofs'],
        stats['soon_notifications'],
        stats['expired_notifications'],
        stats['errors'],
        extra={'request_id': 'job-proof-reminder', 'tenant_id': '-', 'user_id': '-'},
    )

    return stats


