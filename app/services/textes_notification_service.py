from datetime import date, timedelta
from app import db
from app.models import TexteReglementaire, Notification, Utilisateur
from app.utils.notifications import create_notification


class TexteNotificationService:
    @staticmethod
    def notify_new_textes(days=30):
        cutoff = date.today() - timedelta(days=days)
        new_textes = TexteReglementaire.query.filter(
            TexteReglementaire.date_creation >= cutoff
        ).all()
        for texte in new_textes:
            for user in Utilisateur.query.filter_by(actif=True).all():
                create_notification(
                    type='texte',
                    message=f"Nouveau texte réglementaire: {texte.code} - {texte.titre}",
                    utilisateur_id=user.id,
                )
        db.session.commit()

    @staticmethod
    def notify_updated_textes(days=30):
        from app.models import TexteVersion
        cutoff = date.today() - timedelta(days=days)
        updated_versions = TexteVersion.query.filter(
            TexteVersion.date_publication >= cutoff
        ).all()
        for version in updated_versions:
            texte = version.texte
            if not texte:
                continue
            for user in Utilisateur.query.filter_by(actif=True).all():
                create_notification(
                    type='texte',
                    message=f"Mise à jour du texte: {texte.code} - version {version.numero_version}",
                    utilisateur_id=user.id,
                )
        db.session.commit()
