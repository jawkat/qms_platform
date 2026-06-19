from datetime import date, timedelta
from app import db
from app.models import ProofMaster, Notification
from app.utils.notifications import create_notification


def check_expiring_proofs(days_before=30):
    today = date.today()
    cutoff = today + timedelta(days=days_before)
    expiring = ProofMaster.query.filter(
        ProofMaster.validite.isnot(None),
        ProofMaster.validite <= cutoff,
        ProofMaster.validite >= today,
        ProofMaster.statut == 'ACTIF',
    ).all()
    for proof in expiring:
        create_notification(
            type='proof_expiration',
            message=f"La preuve '{proof.nom_fichier}' expire le {proof.validite}.",
            utilisateur_id=proof.uploaded_by or proof.entreprise_id,
        )
    db.session.commit()
    return len(expiring)


def check_expired_proofs():
    today = date.today()
    expired = ProofMaster.query.filter(
        ProofMaster.validite.isnot(None),
        ProofMaster.validite < today,
        ProofMaster.statut == 'ACTIF',
    ).all()
    for proof in expired:
        proof.statut = 'EXPIRE'
        create_notification(
            type='proof_expired',
            message=f"La preuve '{proof.nom_fichier}' a expiré.",
            utilisateur_id=proof.uploaded_by or proof.entreprise_id,
        )
    db.session.commit()
    return len(expired)
