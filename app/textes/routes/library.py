from datetime import date, timedelta
from flask import render_template, request
from flask_login import login_required, current_user
from app import db
from app.models import Domaine, TexteReglementaire, TexteVersion, Article, Secteur, EntrepriseTexte, EvaluationArticle
from app.textes import textes

NEW_DAYS = 30


def _compute_library_linkage(entreprise_id, texte_id, version_active_id):
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


def _render_library(tab, filters):
    eid = current_user.entreprise_id
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
        domaine = db.session.get(Domaine, domaine_id)
        if domaine:
            # Filtrer par domaine_id OU par le champ texte domaine (insensible à la casse)
            query = query.filter(
                db.or_(
                    TexteReglementaire.domaine_id == domaine_id,
                    TexteReglementaire.domaine.ilike(domaine.nom),
                )
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
        link_state = _compute_library_linkage(eid, t.id, v.id if v else None)
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
    per_page = filters.get('per_page', 20)
    page = filters.get('page', 1)
    total_filtered = len(enriched)
    pages = max(1, (total_filtered + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    # Tri : d'abord les liés, puis par date de mise à jour
    def _sort_key(item):
        # linked/evaluated = 0 (premier), unlinked = 1 (après)
        link_order = 0 if item['link_state'] in ('linked', 'evaluated') else 1
        # date de dernière version pour le tri chronologique
        v = item['version_active']
        date_val = v.date_publication if v and v.date_publication else item['texte'].date_creation or date.min
        return (link_order, -(date_val.toordinal() if hasattr(date_val, 'toordinal') else 0))

    enriched.sort(key=_sort_key)

    # Pagination après le tri
    enriched_page = enriched[start:end]

    domaines = Domaine.query.order_by(Domaine.nom).all()
    referentiels = db.session.query(TexteReglementaire.referentiel).distinct().all()
    referentiels = sorted([r[0] for r in referentiels if r[0]])
    secteurs = Secteur.query.order_by(Secteur.nom).all()
    return render_template(
        'textes/library.html',
        tab=tab,
        textes=enriched_page,
        total_textes=total,
        counts=counts,
        filters=filters,
        domaines=domaines,
        referentiels=referentiels,
        secteurs=secteurs,
        per_page=per_page,
        pagination={'page': page, 'pages': pages, 'total': total_filtered},
    )


@textes.route('/bibliotheque')
@textes.route('/bibliotheque/tous-les-textes')
@login_required
def library_all():
    filters = _parse_library_filters()
    filters['status'] = request.args.get('status', 'all')
    return _render_library('all', filters)


@textes.route('/bibliotheque/nouveaux-textes')
@login_required
def library_new():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('new', filters)


@textes.route('/bibliotheque/mises-a-jour-recentes')
@login_required
def library_recent():
    filters = _parse_library_filters()
    filters['status'] = 'all'
    return _render_library('recent', filters)


def _parse_library_filters():
    secteur_ids = request.args.getlist('secteur', type=int)
    return {
        'q': request.args.get('q', ''),
        'domaine_id': request.args.get('domaine_id', type=int),
        'referentiel': request.args.get('referentiel', ''),
        'secteur_ids': secteur_ids,
        'sort': request.args.get('sort', 'updated'),
        'order': request.args.get('order', 'desc'),
        'per_page': request.args.get('per_page', 20, type=int),
        'page': request.args.get('page', 1, type=int),
    }
