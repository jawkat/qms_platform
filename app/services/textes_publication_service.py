from datetime import date, timedelta
from app import db
from app.models import TexteReglementaire, TexteVersion, Article, Domaine


class TextePublicationService:
    @staticmethod
    def get_upcoming_publications(days=30):
        cutoff = date.today() + timedelta(days=days)
        return TexteVersion.query.filter(
            TexteVersion.date_publication.isnot(None),
            TexteVersion.date_publication <= cutoff,
            TexteVersion.date_publication >= date.today(),
            TexteVersion.statut.in_(['projet', 'publication_prevue']),
        ).order_by(TexteVersion.date_publication).all()

    @staticmethod
    def get_recently_published(days=30):
        cutoff = date.today() - timedelta(days=days)
        return TexteReglementaire.query.filter(
            TexteReglementaire.date_creation >= cutoff
        ).order_by(TexteReglementaire.date_creation.desc()).all()

    @staticmethod
    def get_publication_stats():
        total = TexteReglementaire.query.count()
        with_active_version = TexteReglementaire.query.filter(
            TexteReglementaire.version_active_id.isnot(None)
        ).count()
        domaines = Domaine.query.count()
        return {
            'total_textes': total,
            'with_active_version': with_active_version,
            'domaines': domaines,
        }

    @staticmethod
    def get_textes_by_domaine():
        domaines = Domaine.query.all()
        result = []
        for d in domaines:
            count = TexteReglementaire.query.filter_by(domaine_id=d.id).count()
            if count > 0:
                result.append({'domaine': d, 'count': count})
        return result
