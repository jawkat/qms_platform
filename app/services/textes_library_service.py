from datetime import date, timedelta
from flask import request
from app import db
from app.models import Domaine, TexteReglementaire, TexteVersion, Article, Secteur, EntrepriseTexte, EvaluationArticle

NEW_DAYS = 30


def compute_library_linkage(entreprise_id, texte_id, version_active_id):
    if not version_active_id or not entreprise_id:
        return 'unlinked'
    et = EntrepriseTexte.query.filter_by(
        entreprise_id=entreprise_id, texte_version_id=version_active_id
    ).first()
    if not et:
        return 'unlinked'
    eval_count = EvaluationArticle.query.filter_by(entreprise_texte_id=et.id).count()
    eval_done = EvaluationArticle.query.filter(
        EvaluationArticle.entreprise_texte_id == et.id,
        EvaluationArticle.date_evaluation.isnot(None)
    ).count()
    if eval_done > 0:
        return 'evaluated'
    return 'linked'


def build_library_query(filters):
    query = TexteReglementaire.query
    q = filters.get('q', '').strip()
    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                TexteReglementaire.code.ilike(like),
                TexteReglementaire.titre.ilike(like),
                TexteReglementaire.description.ilike(like),
            )
        )
    domaine_id = filters.get('domaine_id')
    if domaine_id:
        query = query.filter(TexteReglementaire.domaine_id == domaine_id)
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
    return query


def enrich_textes_with_linkage(textes, entreprise_id):
    now = date.today()
    cutoff = now - timedelta(days=NEW_DAYS)
    enriched = []
    for t in textes:
        v = t.version_active
        is_new = t.date_creation and t.date_creation.date() >= cutoff if t.date_creation else False
        has_update = v and v.date_publication and v.date_publication >= cutoff if v and v.date_publication else False
        link_state = compute_library_linkage(entreprise_id, t.id, v.id if v else None)
        entreprise_count = EntrepriseTexte.query.filter_by(texte_version_id=v.id).count() if v else 0
        enriched.append({
            'texte': t,
            'version_active': v,
            'is_new': is_new,
            'has_update': has_update,
            'link_state': link_state,
            'entreprise_count': entreprise_count,
        })
    return enriched


def compute_counts(enriched):
    counts = {'all': len(enriched), 'linked': 0, 'unlinked': 0, 'to_evaluate': 0, 'evaluated': 0}
    for item in enriched:
        if item['link_state'] in ('linked', 'evaluated'):
            counts['linked'] += 1
        else:
            counts['unlinked'] += 1
        if item['link_state'] == 'linked':
            counts['to_evaluate'] += 1
        if item['link_state'] == 'evaluated':
            counts['evaluated'] += 1
    return counts


def filter_by_status(enriched, status_filter):
    if status_filter == 'linked':
        return [i for i in enriched if i['link_state'] in ('linked', 'evaluated')]
    elif status_filter == 'unlinked':
        return [i for i in enriched if i['link_state'] == 'unlinked']
    elif status_filter == 'to_evaluate':
        return [i for i in enriched if i['link_state'] == 'linked']
    elif status_filter == 'evaluated':
        return [i for i in enriched if i['link_state'] == 'evaluated']
    return enriched


def paginate(enriched, page=1, per_page=20):
    total_filtered = len(enriched)
    pages = max(1, (total_filtered + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    return enriched[start:end], pages, total_filtered


def get_library_filter_options():
    domaines = Domaine.query.order_by(Domaine.nom).all()
    referentiels_raw = db.session.query(TexteReglementaire.referentiel).distinct().all()
    referentiels = sorted([r[0] for r in referentiels_raw if r[0]])
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return domaines, referentiels, secteurs
