from datetime import date
from app import db
from app.models import TexteVersion, Article


class TexteVersionService:
    @staticmethod
    def get_versions_for_texte(texte_id):
        return TexteVersion.query.filter_by(texte_id=texte_id)\
            .order_by(TexteVersion.numero_version.desc()).all()

    @staticmethod
    def get_active_version(texte):
        if texte.version_active_id:
            return db.session.get(TexteVersion, texte.version_active_id)
        return None

    @staticmethod
    def get_articles_for_version(version_id):
        return Article.query.filter_by(texte_version_id=version_id)\
            .order_by(Article.numero_article).all()

    @staticmethod
    def set_active_version(texte_id, version_id):
        from app.models import TexteReglementaire
        texte = db.session.get(TexteReglementaire, texte_id)
        if texte:
            texte.version_active_id = version_id
            db.session.flush()

    @staticmethod
    def publish_version(version_id):
        version = db.session.get(TexteVersion, version_id)
        if version:
            version.statut = 'active'
            if version.texte:
                version.texte.version_active_id = version.id
            db.session.flush()

    @staticmethod
    def get_version_diff(version_a_id, version_b_id):
        articles_a = {a.numero_article: a for a in TexteVersionService.get_articles_for_version(version_a_id)}
        articles_b = {a.numero_article: a for a in TexteVersionService.get_articles_for_version(version_b_id)}
        added = [a for num, a in articles_b.items() if num not in articles_a]
        removed = [a for num, a in articles_a.items() if num not in articles_b]
        modified = []
        for num in set(articles_a.keys()) & set(articles_b.keys()):
            if articles_a[num].contenu != articles_b[num].contenu:
                modified.append({'old': articles_a[num], 'new': articles_b[num], 'numero': num})
        return {'added': added, 'removed': removed, 'modified': modified}
