"""Service layer pour le module Veille Reglementaire / Bibliotheque."""

from datetime import date, timedelta
from flask import render_template, request, redirect, url_for, jsonify
from flask_login import current_user
from app import db
from app.models import (
    Domaine, TexteReglementaire, TexteVersion, Article, Secteur,
    EntrepriseTexte, EvaluationArticle, ActionCorrective,
    ConformiteEnum, Utilisateur,
)


NEW_DAYS = 30


class VeilleService:
    """Logique metier pour la veille reglementaire."""

    @staticmethod
    def compute_linkage(entreprise_id, texte_id, version_active_id):
        """Determine l'etat de liaison texte-entreprise."""
        if not version_active_id or not entreprise_id:
            return 'unlinked'
        et = EntrepriseTexte.query.filter_by(
            entreprise_id=entreprise_id, texte_version_id=version_active_id
        ).first()
        if not et:
            return 'unlinked'
        eval_done = EvaluationArticle.query.filter(
            EvaluationArticle.entreprise_texte_id == et.id,
            EvaluationArticle.date_evaluation.isnot(None)
        ).count()
        if eval_done > 0:
            return 'evaluated'
        return 'linked'

    @staticmethod
    def get_library_textes(entreprise_id, filters):
        """Recupere et enrichit la liste des textes pour la bibliotheque."""
        query = TexteReglementaire.query
        q = filters.get('q', '').strip()
        if q:
            like = f'%{q}%'
            query = query.filter(
                db.or_(
                    TexteReglementaire.code.ilike(like),
                    TexteReglementaire.titre.ilike(like),
                    TexteReglementaire.description.ilike(like))
            )
        domaine_id = filters.get('domaine_id')
        if domaine_id:
            domaine = db.session.get(Domaine, domaine_id)
            if domaine:
                query = query.filter(
                    db.or_(
                        TexteReglementaire.domaine_id == domaine_id,
                        TexteReglementaire.domaine.ilike(domaine.nom))
                )
        referentiel = filters.get('referentiel')
        if referentiel:
            query = query.filter(TexteReglementaire.referentiel == referentiel)
        secteur_ids = filters.get('secteur_ids', [])
        if secteur_ids:
            query = query.filter(TexteReglementaire.secteurs.any(Secteur.id.in_(secteur_ids)))
        sort = filters.get('sort', 'updated')
        if sort == 'code':
            query = query.order_by(TexteReglementaire.code)
        elif sort == 'title':
            query = query.order_by(TexteReglementaire.titre)
        elif sort == 'domain':
            query = query.order_by(TexteReglementaire.domaine)
        else:
            query = query.order_by(TexteReglementaire.date_creation.desc())

        all_textes = query.all()
        total = len(all_textes)
        now = date.today()
        cutoff = now - timedelta(days=NEW_DAYS)

        counts = {'all': total, 'linked': 0, 'unlinked': 0, 'to_evaluate': 0, 'evaluated': 0}
        enriched = []
        for t in all_textes:
            v = t.version_active
            is_new = t.date_creation and t.date_creation.date() >= cutoff if t.date_creation else False
            has_update = v and v.date_publication and v.date_publication >= cutoff if v and v.date_publication else False
            link_state = VeilleService.compute_linkage(entreprise_id, t.id, v.id if v else None)
            entreprise_count = EntrepriseTexte.query.filter_by(texte_version_id=v.id).count() if v else 0
            if link_state in ('linked', 'evaluated'):
                counts['linked'] += 1
            else:
                counts['unlinked'] += 1
            if link_state == 'linked':
                counts['to_evaluate'] += 1
            if link_state == 'evaluated':
                counts['evaluated'] += 1
            enriched.append({
                'texte': t,
                'version_active': v,
                'is_new': is_new,
                'has_update': has_update,
                'link_state': link_state,
                'entreprise_count': entreprise_count,
            })

        status_filter = filters.get('status', 'all')
        if status_filter == 'linked':
            enriched = [i for i in enriched if i['link_state'] in ('linked', 'evaluated')]
        elif status_filter == 'unlinked':
            enriched = [i for i in enriched if i['link_state'] == 'unlinked']
        elif status_filter == 'to_evaluate':
            enriched = [i for i in enriched if i['link_state'] == 'linked']
        elif status_filter == 'evaluated':
            enriched = [i for i in enriched if i['link_state'] == 'evaluated']

        def _sort_key(item):
            link_order = 0 if item['link_state'] in ('linked', 'evaluated') else 1
            v = item['version_active']
            date_val = v.date_publication if v and v.date_publication else item['texte'].date_creation or date.min
            return (link_order, -(date_val.toordinal() if hasattr(date_val, 'toordinal') else 0))

        enriched.sort(key=_sort_key)
        return enriched, total, counts

    @staticmethod
    def paginate(enriched, page, per_page):
        """Page la liste enrichie."""
        total_filtered = len(enriched)
        pages = max(1, (total_filtered + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        return enriched[start:end], total_filtered, pages

    @staticmethod
    def get_article_nc_context(entreprise_id, article_id):
        """Recupere le contexte NC pour un article."""
        from app.models.nonconformite import NonConformite as NCModel

        ev_q = EvaluationArticle.query.join(EntrepriseTexte).filter(
            EntrepriseTexte.entreprise_id == entreprise_id,
            EvaluationArticle.conforme == ConformiteEnum.NON_CONFORME,
        )
        evals = ev_q.order_by(EvaluationArticle.date_evaluation.desc().nullslast()).all()
        nc_eval_ids = {nc.evaluation_id for nc in NCModel.query.filter_by(entreprise_id=entreprise_id).all() if nc.evaluation_id}
        nc_evs = [ev for ev in evals if ev.id not in nc_eval_ids]

        evaluation = None
        for ev in nc_evs:
            if ev.article_id == article_id:
                evaluation = ev
                break

        nc_articles = [ev.article_id for ev in nc_evs]
        current_idx = nc_articles.index(article_id) if article_id in nc_articles else -1
        next_article_id = nc_articles[current_idx + 1] if current_idx >= 0 and current_idx < len(nc_articles) - 1 else None
        prev_article_id = nc_articles[current_idx - 1] if current_idx > 0 else None

        stats = {
            'total': len(nc_evs),
            'current': current_idx + 1 if current_idx >= 0 else 0,
            'conforme': 0,
            'non_conforme': len(nc_evs),
            'non_applicable': 0,
            'evalue': len(nc_evs),
        }

        return nc_evs, evaluation, next_article_id, prev_article_id, stats

    @staticmethod
    def save_article_evaluation(evaluation, form_data, user_id):
        """Sauvegarde l'evaluation d'un article."""
        from datetime import datetime as dt

        conforme_val = form_data.get('conforme')
        if conforme_val:
            evaluation.conforme = ConformiteEnum[conforme_val]
        applicable_val = form_data.get('applicable')
        if applicable_val:
            from app.models.conformite import ApplicabiliteEnum
            evaluation.applicable = ApplicabiliteEnum[applicable_val]
        evaluation.observation = form_data.get('observation', evaluation.observation)
        evaluation.date_evaluation = dt.utcnow()
        evaluation.evalue_par = user_id
        db.session.commit()

    @staticmethod
    def get_article_proofs_and_actions(evaluation):
        """Recupere les preuves et actions lies a une evaluation."""
        from app.models.proofs import ProofReference

        proofs = []
        actions = []
        if evaluation:
            refs = ProofReference.query.filter_by(
                entity_type='evaluation_article', entity_id=evaluation.id
            ).all()
            for r in refs:
                proofs.append({
                    'id': r.id,
                    'proof_id': r.proof_master_id,
                    'nom_fichier': r.proof_master.nom_fichier if r.proof_master else '?',
                    'date_attached': r.date_attached.strftime('%d/%m/%Y') if r.date_attached else '',
                })
            actions = ActionCorrective.query.filter_by(
                source_type='evaluation_article', source_id=evaluation.id
            ).order_by(ActionCorrective.date_creation.desc()).all()
        return proofs, actions
