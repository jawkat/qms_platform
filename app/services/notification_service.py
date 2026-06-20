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
    def notify(utilisateur_id, category, message, urgence='normale', entite_type=None, entite_id=None):
        """
        Envoie une notification à un utilisateur spécifique si ses préférences le permettent.
        """
        user = db.session.get(Utilisateur, utilisateur_id)
        if not user:
            return False

        # 1. Vérifier si le module lié à la catégorie est actif pour l'entreprise
        if category not in ['systeme', 'general', 'technique']:
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
                utilisateur_id=utilisateur_id,
                message=message,
                categorie=category,
                urgence=urgence,
                entite_type=entite_type,
                entite_id=entite_id,
                lu=False
            )
            db.session.add(notif)

        # 4. Notification Email (via Task Queue pour ne pas bloquer le thread principal)
        if email_enabled and user.email:
            NotificationService._enqueue_email(user, category, message, urgence)

        db.session.commit()
        return True

    @staticmethod
    def notify_managers(entreprise_id, category, message, urgence='normale', entite_type=None, entite_id=None):
        """
        Alerte tous les managers/admins d'une entreprise pour un incident ou un événement de supervision.
        """
        managers = Utilisateur.query.join(Utilisateur.role).filter(
            Utilisateur.entreprise_id == entreprise_id,
            (Utilisateur.role.nom == 'Manager') | (Utilisateur.role.est_systeme == True),
            Utilisateur.actif == True
        ).all()

        for manager in managers:
            NotificationService.notify(manager.id, category, message, urgence, entite_type, entite_id)

    @staticmethod
    def notify_system_admins(category, message, urgence='haute', entite_type=None, entite_id=None):
        """
        Alerte tous les administrateurs globaux (est_systeme) de la plateforme.
        """
        from app.models.auth import Role, Utilisateur
        try:
            current_app.logger.info(f"NotificationService: Alerte technique reçue: {message[:50]}...")
            # On s'assure d'avoir une session propre pour la lecture
            db.session.remove()
            
            admins = db.session.query(Utilisateur).join(Role, Utilisateur.role_id == Role.id).filter(
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
                    NotificationService.notify(admin.id, category, message, urgence, entite_type, entite_id)
                except Exception as ex:
                    current_app.logger.error(f"Echec envoi individuel à {admin.email}: {str(ex)}")

            # Un commit final pour être sûr
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Bug critique dans NotificationService: {str(e)}")
            db.session.rollback()

    @staticmethod
    def _enqueue_email(user, category, message, urgence):
        """
        Délègue l'envoi de l'email au worker background.
        """
        try:
            # On utilise le système de tâches déjà en place (RQ ou Celery supposé)
            # Pour l'instant, on simule l'appel ou on utilise flask-mail directement si configuré
            from app.utils.notifications import send_email_notification_task
            send_email_notification_task(
                email=user.email,
                name=f"{user.prenom} {user.nom}",
                category=category,
                message=message,
                urgence=urgence
            )
        except ImportError:
            current_app.logger.warning("NotificationService: utils.notifications non trouvé, email non envoyé.")
        except Exception as e:
            current_app.logger.error(f"Erreur envoi email: {str(e)}")

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
