from datetime import date, datetime, timedelta
from flask import current_app, render_template
from app import db
from app.models.actions import ActionCorrective
from app.models.nonconformite import NonConformite
from app.models.proofs import ProofMaster
from app.models.systeme import Notification, TacheSysteme
from app.models.entreprise import Entreprise
from app.models.auth import Utilisateur
from app.utils.notifications import create_notification


def run_daily_alerts():
    """Point d'entrée principal pour les alertes quotidiennes."""
    results = {
        'actions_overdue': 0,
        'actions_echeance': 0,
        'nc_overdue': 0,
        'documents_expired': 0,
        'documents_expiring': 0,
        'notifications_sent': 0,
        'emails_enqueued': 0,
    }

    try:
        results['actions_overdue'] = _alert_overdue_actions()
        results['actions_echeance'] = _alert_upcoming_action_deadlines()
        results['nc_overdue'] = _alert_overdue_nc()
        results['documents_expired'] = _alert_expired_documents()
        results['documents_expiring'] = _alert_expiring_documents()

        results['notifications_sent'] = (
            results['actions_overdue'] + results['actions_echeance']
            + results['nc_overdue'] + results['documents_expired']
            + results['documents_expiring']
        )

        _log_task('daily_alerts', 'succes', results)
    except Exception as e:
        current_app.logger.exception('Erreur alertes quotidiennes')
        _log_task('daily_alerts', 'erreur', {'error': str(e)})

    return results


def _alert_overdue_actions():
    """Alerte les actions dépassées."""
    today = date.today()
    actions = ActionCorrective.query.filter(
        ActionCorrective.date_echeance < today,
        ActionCorrective.statut.in_(['A_FAIRE', 'EN_COURS']),
    ).all()

    count = 0
    for action in actions:
        if action.responsable_id:
            jours_retard = (today - action.date_echeance).days
            msg = (
                f"Action en retard : {action.description[:80]} "
                f"({jours_retard} jour(s) de retard, échéance {action.date_echeance.strftime('%d/%m/%Y')})"
            )
            create_notification(action.responsable_id, msg, type='overdue', entite_id=action.id, entite_type='action')
            _send_alert_email(action.responsable, 'Action en retard', msg)
            count += 1

    return count


def _alert_upcoming_action_deadlines():
    """Alerte les actions proches de l'échéance (7j, 3j, aujourd'hui)."""
    today = date.today()
    horizons = [today, today + timedelta(days=3), today + timedelta(days=7)]
    count = 0

    for horizon in horizons:
        actions = ActionCorrective.query.filter(
            ActionCorrective.date_echeance == horizon,
            ActionCorrective.statut.in_(['A_FAIRE', 'EN_COURS']),
        ).all()

        for action in actions:
            if action.responsable_id:
                jours_restants = (horizon - today).days
                if jours_restants == 0:
                    msg = f"Échéance aujourd'hui : {action.description[:80]}"
                else:
                    msg = f"Échéance dans {jours_restants} jour(s) : {action.description[:80]}"
                create_notification(action.responsable_id, msg, type='echeance', entite_id=action.id, entite_type='action')
                _send_alert_email(action.responsable, 'Échéance action', msg)
                count += 1

    return count


def _alert_overdue_nc():
    """Alerte les non-conformités non clôturées depuis > 30 jours."""
    seuil = date.today() - timedelta(days=30)
    ncs = NonConformite.query.filter(
        NonConformite.statut.in_(['ouverte', 'en_cours']),
        NonConformite.date_creation < datetime.combine(seuil, datetime.min.time()),
    ).all()

    count = 0
    for nc in ncs:
        if nc.responsable_id:
            msg = f"NC non clôturée depuis > 30j : {nc.description[:80]}"
            create_notification(nc.responsable_id, msg, type='overdue', entite_id=nc.id, entite_type='nonconformite')
            _send_alert_email(nc.responsable, 'NC en retard', msg)
            count += 1

    return count


def _alert_expired_documents():
    """Alerte les documents dont la validité a expiré."""
    today = date.today()
    docs = ProofMaster.query.filter(
        ProofMaster.statut == 'ACTIF',
        ProofMaster.validite.isnot(None),
        ProofMaster.validite < today,
    ).all()

    count = 0
    for doc in docs:
        if doc.upload_par:
            msg = f"Document expiré : {doc.nom_fichier} (validité {doc.validite.strftime('%d/%m/%Y')})"
            create_notification(doc.upload_par, msg, type='alerte', entite_id=doc.id, entite_type='document')
            user = Utilisateur.query.get(doc.upload_par)
            _send_alert_email(user, 'Document expiré', msg)
            count += 1

    return count


def _alert_expiring_documents():
    """Alerte les documents qui expirent dans les 30 prochains jours."""
    today = date.today()
    limite = today + timedelta(days=30)
    docs = ProofMaster.query.filter(
        ProofMaster.statut == 'ACTIF',
        ProofMaster.validite.isnot(None),
        ProofMaster.validite >= today,
        ProofMaster.validite <= limite,
    ).all()

    count = 0
    for doc in docs:
        if doc.upload_par:
            jours_restants = (doc.validite - today).days
            msg = (
                f"Document expire dans {jours_restants}j : {doc.nom_fichier} "
                f"(validité {doc.validite.strftime('%d/%m/%Y')})"
            )
            create_notification(doc.upload_par, msg, type='echeance', entite_id=doc.id, entite_type='document')
            user = Utilisateur.query.get(doc.upload_par)
            _send_alert_email(user, 'Document expire bientôt', msg)
            count += 1

    return count


def _send_alert_email(user, subject, message):
    """Envoie un email d'alerte via RQ (asynchrone)."""
    try:
        if not user or not user.email:
            return
        from app.jobs.scheduler import enqueue_email
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#e63946;color:#fff;padding:20px;text-align:center;">
                <h2 style="margin:0;">QMS Platform — Alerte</h2>
            </div>
            <div style="padding:20px;background:#f5f6fa;">
                <p>Bonjour {user.prenom},</p>
                <div style="background:#fff;border-left:4px solid #e63946;padding:15px;margin:15px 0;">
                    {message}
                </div>
                <p><a href="http://localhost:5006/tableau-de-bord" style="display:inline-block;background:#e63946;color:#fff;padding:10px 20px;text-decoration:none;border-radius:5px;">Voir le tableau de bord</a></p>
                <p style="color:#999;font-size:12px;">Cet email est envoyé automatiquement par QMS Platform.</p>
            </div>
        </div>
        """
        enqueue_email(
            subject=f'[QMS] {subject}',
            recipients=[user.email],
            html=html,
            priority='high',
        )
    except Exception as e:
        current_app.logger.error(f'Failed to enqueue alert email: {e}')


def _log_task(type_tache, statut, resultat):
    """Enregistre l'exécution de la tâche dans JournalSecurite."""
    try:
        tache = TacheSysteme(
            type_tache=type_tache,
            date_execution=datetime.utcnow(),
            statut=statut,
            resultat=str(resultat),
        )
        db.session.add(tache)
        db.session.commit()
    except Exception:
        db.session.rollback()
