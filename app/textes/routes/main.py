from flask import render_template, request, jsonify
from flask_login import login_required
from app import db
from app.models import Domaine, TexteReglementaire, TexteVersion, Article
from app.textes import textes
from app.utils.permissions import system_admin_required
from app.utils.permissions import has_permission
from sqlalchemy import func


@textes.route('/')
@login_required
@system_admin_required
def index():
    query = TexteReglementaire.query
    domaine_id = request.args.get('domaine', type=int)
    type_filter = request.args.get('type')
    search = request.args.get('search')
    if domaine_id:
        query = query.filter(TexteReglementaire.domaine_id == domaine_id)
    if type_filter:
        query = query.filter(TexteReglementaire.type == type_filter)
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                TexteReglementaire.titre.ilike(like),
                TexteReglementaire.code.ilike(like),
                TexteReglementaire.description.ilike(like),
            )
        )
    textes_list = query.order_by(TexteReglementaire.code).all()
    domaines = Domaine.query.order_by(Domaine.nom).all()
    types = [r[0] for r in db.session.query(TexteReglementaire.type).distinct().filter(TexteReglementaire.type.isnot(None)).order_by(TexteReglementaire.type).all()]
    filters = {}
    if domaine_id:
        filters['domaine'] = domaine_id
    if type_filter:
        filters['type'] = type_filter
    if search:
        filters['search'] = search
    return render_template('textes/index.html', textes=textes_list, domaines=domaines, types=types, filters=filters)


@textes.route('/<int:texte_id>')
@login_required
@has_permission('textes.voir')
def detail(texte_id):
    from flask_login import current_user
    texte = TexteReglementaire.query.get_or_404(texte_id)
    # Lecteurs → redirect direct à la version active
    if not (current_user.role and current_user.role.est_systeme):
        if texte.version_active_id:
            return redirect(url_for('textes.version_detail', version_id=texte.version_active_id))
        return redirect(url_for('textes.library_all'))
    versions = TexteVersion.query.filter_by(texte_id=texte_id).order_by(TexteVersion.numero_version.desc()).all()
    articles = []
    if texte.version_active_id:
        articles = Article.query.filter_by(texte_version_id=texte.version_active_id).order_by(Article.numero_article).all()
    return render_template('textes/detail.html', texte=texte, versions=versions, articles=articles)


@textes.route('/version/<int:version_id>')
@login_required
@has_permission('textes.voir')
def version_detail(version_id):
    from flask_login import current_user
    from app.models.conformite import EntrepriseTexte
    version = TexteVersion.query.get_or_404(version_id)
    articles = Article.query.filter_by(texte_version_id=version_id).order_by(Article.numero_article).all()
    linked = False
    if current_user.entreprise_id:
        linked = EntrepriseTexte.query.filter_by(
            entreprise_id=current_user.entreprise_id,
            texte_version_id=version_id
        ).first() is not None
    return render_template('textes/version_detail.html', version=version, articles=articles, linked=linked)


@textes.route('/api/liste')
@login_required
def api_liste():
    textes_list = TexteReglementaire.query.order_by(TexteReglementaire.code).all()
    data = []
    for t in textes_list:
        data.append({
            'id': t.id,
            'code': t.code,
            'titre': t.titre,
            'type': t.type,
            'domaine': t.domaine,
            'domaine_id': t.domaine_id,
            'sousdomaine': t.sousdomaine,
            'theme': t.theme,
            'referentiel': t.referentiel,
            'version_active_id': t.version_active_id,
            'date_creation': t.date_creation.isoformat() if t.date_creation else None,
        })
    return jsonify(data)


@textes.route('/api/domaines')
@login_required
def api_domaines():
    domaines = Domaine.query.order_by(Domaine.nom).all()
    data = [{'id': d.id, 'nom': d.nom, 'description': d.description} for d in domaines]
    return jsonify(data)


@textes.route('/api/<int:texte_id>')
@login_required
def api_texte(texte_id):
    texte = TexteReglementaire.query.get_or_404(texte_id)
    versions = TexteVersion.query.filter_by(texte_id=texte_id).order_by(TexteVersion.numero_version.desc()).all()
    return jsonify({
        'id': texte.id,
        'code': texte.code,
        'titre': texte.titre,
        'description': texte.description,
        'type': texte.type,
        'domaine': texte.domaine,
        'domaine_id': texte.domaine_id,
        'sousdomaine': texte.sousdomaine,
        'theme': texte.theme,
        'referentiel': texte.referentiel,
        'version_active_id': texte.version_active_id,
        'versions': [{
            'id': v.id,
            'numero_version': v.numero_version,
            'date_publication': v.date_publication.isoformat() if v.date_publication else None,
            'preambule': v.preambule,
            'statut': v.statut,
        } for v in versions],
        'date_creation': texte.date_creation.isoformat() if texte.date_creation else None,
    })
