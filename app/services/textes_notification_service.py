from app.services.notification_service import NotificationService


def get_linked_user_ids_for_texte(texte_id, exclude_user_id=None):
    from app import db
    from app.models import TexteVersion, EntrepriseTexte, Utilisateur

    version_ids = [row[0] for row in db.session.query(TexteVersion.id).filter_by(texte_id=texte_id).all()]
    if not version_ids:
        return []

    entreprise_ids = {
        row[0]
        for row in db.session.query(EntrepriseTexte.entreprise_id)
        .filter(EntrepriseTexte.texte_version_id.in_(version_ids))
        .distinct()
        .all()
    }
    if not entreprise_ids:
        return []

    query = Utilisateur.query.filter(
        Utilisateur.entreprise_id.in_(entreprise_ids),
        Utilisateur.actif == True,
    )
    if exclude_user_id:
        query = query.filter(Utilisateur.id != exclude_user_id)

    return [row[0] for row in query.with_entities(Utilisateur.id).all()]


def notify_regulation_update(texte, update_label, actor_user_id=None, change_description=None):
    if not texte:
        return

    recipient_user_ids = get_linked_user_ids_for_texte(texte.id, exclude_user_id=actor_user_id)
    if not recipient_user_ids:
        return

    message = (
        f"Mise à jour réglementaire: {update_label} sur le texte '{texte.titre}' "
        f"(code: {texte.code or 'N/A'})."
    )

    change_description = (change_description or '').strip()
    if change_description:
        message = f"{message}\nDétail : {change_description}"

    NotificationService.notify_users(
        user_ids=recipient_user_ids,
        category='veille',
        message=message,
        urgence='normale',
        entite_type='texte',
        entite_id=texte.id,
        notification_type='texte',
    )
