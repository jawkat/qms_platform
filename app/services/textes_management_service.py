from datetime import datetime
from app import db
from app.models import TexteReglementaire, TexteVersion, Article, ExigenceType, NiveauRisqueType, Secteur


class TexteManagementService:
    @staticmethod
    def create_texte(code, titre, type_texte=None, description=None, domaine=None,
                     domaine_id=None, sousdomaine=None, theme=None, referentiel=None,
                     secteur_ids=None):
        texte = TexteReglementaire(
            code=code, titre=titre, type=type_texte, description=description,
            domaine=domaine, domaine_id=domaine_id, sousdomaine=sousdomaine,
            theme=theme, referentiel=referentiel,
        )
        db.session.add(texte)
        if secteur_ids:
            secteurs = Secteur.query.filter(Secteur.id.in_(secteur_ids)).all()
            texte.secteurs.extend(secteurs)
        db.session.flush()
        return texte

    @staticmethod
    def update_texte(texte, **kwargs):
        for field in ('code', 'titre', 'type', 'description', 'domaine',
                      'domaine_id', 'sousdomaine', 'theme', 'referentiel'):
            if field in kwargs:
                setattr(texte, field, kwargs[field])
        if 'secteur_ids' in kwargs:
            secteur_ids = kwargs['secteur_ids']
            texte.secteurs = Secteur.query.filter(Secteur.id.in_(secteur_ids)).all() if secteur_ids else []
        db.session.flush()
        return texte

    @staticmethod
    def delete_texte(texte):
        TexteVersion.query.filter_by(texte_id=texte.id).delete()
        db.session.delete(texte)
        db.session.flush()

    @staticmethod
    def create_version(texte_id, numero_version, date_publication=None, preambule=None,
                       commentaire_version=None, statut='projet', cree_par=None,
                       version_precedente_id=None, set_active=False):
        version = TexteVersion(
            texte_id=texte_id, numero_version=numero_version,
            date_publication=date_publication, preambule=preambule,
            commentaire_version=commentaire_version, statut=statut,
            cree_par=cree_par, version_precedente_id=version_precedente_id,
        )
        db.session.add(version)
        db.session.flush()
        if set_active:
            texte = db.session.get(TexteReglementaire, texte_id)
            if texte:
                texte.version_active_id = version.id
                db.session.flush()
        return version

    @staticmethod
    def create_article(version_id, numero_article, contenu,
                       exigence_type=ExigenceType.INFORMATION,
                       niveau_risque=NiveauRisqueType.FAIBLE,
                       resume_article=None, explication_detaillee=None,
                       preuve_conformite=None, acteur=None):
        article = Article(
            texte_version_id=version_id, numero_article=numero_article,
            contenu=contenu, exigence_type=exigence_type,
            niveau_risque=niveau_risque, resume_article=resume_article,
            explication_detaillee=explication_detaillee,
            preuve_conformite=preuve_conformite, acteur=acteur,
        )
        db.session.add(article)
        db.session.flush()
        return article

    @staticmethod
    def update_article(article, **kwargs):
        for field in ('numero_article', 'contenu', 'resume_article',
                      'explication_detaillee', 'preuve_conformite', 'acteur'):
            if field in kwargs:
                setattr(article, field, kwargs[field])
        if 'exigence_type' in kwargs:
            article.exigence_type = (
                ExigenceType[kwargs['exigence_type']]
                if isinstance(kwargs['exigence_type'], str)
                else kwargs['exigence_type']
            )
        if 'niveau_risque' in kwargs:
            article.niveau_risque = (
                NiveauRisqueType[kwargs['niveau_risque']]
                if isinstance(kwargs['niveau_risque'], str)
                else kwargs['niveau_risque']
            )
        db.session.flush()
        return article
