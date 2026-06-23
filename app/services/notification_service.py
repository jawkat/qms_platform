"""
QMS Platform — NotificationService
====================================
Service central de distribution des notifications In-App et Email.

Architecture
------------
Chaque notification suit le pipeline suivant :

    1. [Module actif ?]  — Vérifie que le module métier est activé pour
                           l'entreprise de l'utilisateur.  Si non → abandon.
    2. [Préférences]     — Charge NotificationPreference(utilisateur, categorie).
                           Si aucune préférence → active par défaut pour les
                           urgences haute/critique.
    3. [In-App]          — Écrit un enregistrement Notification en base via
                           db.session.flush() (pas de commit : l'appelant
                           contrôle la transaction).
    4. [Email async]     — Si email_enabled, enfile un job RQ (queue 'high'
                           pour haute/critique, 'default' sinon) pour ne pas
                           bloquer le thread HTTP.

Usage rapide
------------
::

    from app.services.notification_service import NotificationService

    # Notifier un utilisateur spécifique
    NotificationService.notify(
        utilisateur_id=user.id,
        category='hse',
        message="Incident déclaré : chute de plain-pied.",
        urgence='haute',
        entite_type='incident',
        entite_id=incident.id,
    )
    db.session.commit()           # l'appelant commit

    # Notifier tous les managers d'une entreprise
    NotificationService.notify_managers(
        entreprise_id=3,
        category='hse',
        message="Alerte EPI expirée.",
    )

    # Notifier tous les admins système (monitoring technique)
    NotificationService.notify_system_admins(
        category='technique',
        message="Bug applicatif détecté : 500 sur /actions/123",
        urgence='haute',
    )

Catégories reconnues
--------------------
- ``hse``       : incidents, accidents, EPI
- ``qualite``   : NC, CAPA, audits, documents
- ``general``   : actions, échéances, alertes diverses
- ``systeme``   : sécurité, connexions suspectes
- ``technique`` : bugs, erreurs 500/404 (admins système uniquement)
- ``veille``    : textes réglementaires, conformité
- ``support``   : tickets

Note sur les transactions
-------------------------
``notify()`` utilise ``db.session.flush()`` et NON ``commit()``.
Cela garantit que la notification est persistée dans la même transaction
que les données métier de l'appelant, permettant un rollback cohérent
en cas d'erreur.
"""
from flask import current_app, render_template
from datetime import datetime
from app import db
from app.models.systeme import Notification, NotificationPreference
from app.models.auth import Utilisateur
from app.core import plugin_manager


class NotificationService:
    """
    Système central de distribution des notifications (In-App et Email).
    Gère les préférences utilisateurs et le filtrage par module.
    """

    @staticmethod
    def notify(utilisateur_id, category, message, urgence='normale', entite_type=None, entite_id=None, notification_type=None, skip_module_check=False):
        """
        Envoie une notification à un utilisateur spécifique si ses préférences le permettent.
        """
        user = db.session.get(Utilisateur, utilisateur_id)
        if not user:
            return False

        # 1. Vérifier si le module lié à la catégorie est actif pour l'entreprise
        if not skip_module_check and category not in ['systeme', 'general', 'technique']:
            if not plugin_manager.is_active(category, user.entreprise_id):
                return False

        # 2. Récupérer les préférences de l'utilisateur
        prefs = NotificationPreference.query.filter_by(
            utilisateur_id=utilisateur_id, 
            categorie=category
        ).first()

        # Si pas de préférences, on active par défaut pour les urgences hautes/critiques
        app_enabled = prefs.app_enabled if prefs else True
        email_enabled = prefs.email_enabled if prefs else (urgence in ['haute', 'critique'])

        # 3. Notification In-App
        if app_enabled:
            notif = Notification(
                type=notification_type,
                utilisateur_id=utilisateur_id,
                message=message,
                categorie=category,
                urgence=urgence,
                entite_type=entite_type,
                entite_id=entite_id,
                lu=False
            )
            db.session.add(notif)

        # 4. Notification Email
        if email_enabled and user.email:
            NotificationService._enqueue_email(user, category, message, urgence)

        db.session.commit()
        return True

    @staticmethod
    def notify_managers(entreprise_id, category, message, urgence='normale', entite_type=None, entite_id=None, notification_type=None):
        """
        Alerte tous les managers/admins d'une entreprise pour un incident ou un événement de supervision.
        """
        managers = Utilisateur.query.join(Utilisateur.role).filter(
            Utilisateur.entreprise_id == entreprise_id,
            (Utilisateur.role.nom == 'Manager') | (Utilisateur.role.est_systeme == True),
            Utilisateur.actif == True
        ).all()

        for manager in managers:
            NotificationService.notify(manager.id, category, message, urgence, entite_type, entite_id, notification_type)

    @staticmethod
    def notify_system_admins(category, message, urgence='haute', entite_type=None, entite_id=None, notification_type=None):
        """
        Alerte tous les administrateurs globaux (est_systeme) de la plateforme.
        """
        from app.models.auth import Role, Utilisateur
        try:
            current_app.logger.info(f"NotificationService: Alerte technique reçue: {message[:50]}...")

            admins = Utilisateur.query.join(Role, Utilisateur.role_id == Role.id).filter(
                Role.est_systeme == True,
                Utilisateur.actif == True
            ).all()

            if not admins:
                current_app.logger.error("NotificationService: AUCUN ADMIN SYSTEME TROUVE. Utilisation du fallback email.")
                emergency_email = current_app.config.get('MAIL_ADMIN_EMAIL')
                if emergency_email:
                    from app.utils.notifications import send_email_notification_task
                    send_email_notification_task(emergency_email, "Super Admin", category, message, urgence)
                return

            current_app.logger.info(f"NotificationService: {len(admins)} admins à notifier.")
            for admin in admins:
                try:
                    NotificationService.notify(admin.id, category, message, urgence, entite_type, entite_id, notification_type)
                except Exception as ex:
                    current_app.logger.error(f"Echec envoi individuel à admin #{admin.id}: {str(ex)}")

        except Exception as e:
            current_app.logger.error(f"Bug critique dans NotificationService: {str(e)}")

    @staticmethod
    def notify_enterprise_users(entreprise_id, category, message, urgence='normale', exclude_user_id=None, entite_type=None, entite_id=None, notification_type=None):
        """
        Notifie tous les utilisateurs actifs d'une entreprise.
        """
        query = Utilisateur.query.filter(
            Utilisateur.entreprise_id == entreprise_id,
            Utilisateur.actif == True,
        )
        if exclude_user_id:
            query = query.filter(Utilisateur.id != exclude_user_id)
        users = query.all()
        for user in users:
            NotificationService.notify(user.id, category, message, urgence, entite_type, entite_id, notification_type)

    @staticmethod
    def notify_users(user_ids, category, message, urgence='normale', entite_type=None, entite_id=None, notification_type=None):
        """
        Notifie une liste d'utilisateurs par leurs IDs.
        """
        for uid in user_ids:
            NotificationService.notify(uid, category, message, urgence, entite_type, entite_id, notification_type)

    @staticmethod
    def _enqueue_email(user, category, message, urgence):
        """
        Envoie l'email de notification — d'abord par RQ (async), puis synchrone si Redis est indisponible.
        """
        sent = False
        # 1. Tentative asynchrone via RQ
        try:
            from redis import Redis
            from rq import Queue
            from app.utils.notifications import send_email_notification_task

            url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            conn = Redis.from_url(url)
            conn.ping()
            queue_name = 'high' if urgence in ['haute', 'critique'] else 'default'
            q = Queue(queue_name, connection=conn)
            entreprise_nom = user.entreprise.nom if user.entreprise else None
            user_role = user.role.nom if user.role else None

            q.enqueue(
                send_email_notification_task,
                email=user.email,
                name=f"{user.prenom} {user.nom}",
                category=category,
                message=message,
                urgence=urgence,
                entreprise_nom=entreprise_nom,
                user_role=user_role,
            )
            current_app.logger.info("Email notification enqueued in RQ for %s", user.email)
            sent = True
        except Exception as e:
            current_app.logger.warning(f"Redis indisponible pour {user.email}, envoi synchrone: {str(e)}")

        # 2. Fallback synchrone si Redis est down
        if not sent:
            try:
                from app.utils.notifications import send_email_notification_task
                entreprise_nom = user.entreprise.nom if user.entreprise else None
                user_role = user.role.nom if user.role else None
                send_email_notification_task(
                    email=user.email,
                    name=f"{user.prenom} {user.nom}",
                    category=category,
                    message=message,
                    urgence=urgence,
                    entreprise_nom=entreprise_nom,
                    user_role=user_role,
                )
                sent = True
            except Exception as e:
                current_app.logger.error(f"Échec envoi email synchrone à {user.email}: {str(e)}")
                try:
                    from flask import flash
                    flash(f"Échec d'envoi d'email de notification à {user.email}. Vérifiez la config mail.", 'warning')
                except RuntimeError:
                    pass

        return sent

    @staticmethod
    def get_unread_count(utilisateur_id):
        return Notification.query.filter_by(utilisateur_id=utilisateur_id, lu=False).count()

    @staticmethod
    def mark_as_read(notification_id, utilisateur_id):
        notif = Notification.query.filter_by(id=notification_id, utilisateur_id=utilisateur_id).first()
        if notif:
            notif.lu = True
            db.session.commit()
            return True
        return False
