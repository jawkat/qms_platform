from flask import render_template, request, jsonify
from flask_login import current_user
from app import db
from app.models import Veille, SourceReglementaire, TexteReglementaire
from app.veille import veille
from app.utils.permissions import system_admin_required, access_required
from datetime import date
from app.utils.base_resource import BaseResource


class VeilleResource(BaseResource):
    model = Veille
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})


class SourceReglementaireResource(BaseResource):
    model = SourceReglementaire
    protected_fields = frozenset({'id', 'date_creation'})
    tenant_field = None


@veille.route('/')
@access_required(permission='textes.voir')
@system_admin_required
def index():
    sources = SourceReglementaire.query.order_by(SourceReglementaire.nom).all()
    statut = request.args.get('statut')
    q = Veille.query
    if statut:
        q = q.filter(Veille.statut == statut)
    veilles = q.order_by(Veille.date_detection.desc()).all()
    textes = TexteReglementaire.query.order_by(TexteReglementaire.titre).all()
    return render_template('veille/index.html', sources=sources, veilles=veilles,
                           textes=textes, filters=request.args)


@veille.route('/<int:veille_id>')
@access_required(permission='textes.voir')
@system_admin_required
def detail(veille_id):
    v = Veille.query.get_or_404(veille_id)
    return render_template('veille/detail.html', veille=v)


@veille.route('/api/liste')
@access_required(permission='textes.voir')
@system_admin_required
def api_liste():
    veilles = Veille.query.order_by(Veille.date_detection.desc()).all()
    return jsonify([{
        'id': v.id,
        'texte_id': v.texte_id,
        'texte_titre': v.texte.titre if v.texte else '',
        'source_id': v.source_id,
        'source_nom': v.source.nom if v.source else '',
        'date_detection': v.date_detection.isoformat() if v.date_detection else None,
        'statut': v.statut,
        'resume': v.resume,
        'lien_source': v.lien_source,
        'date_creation': v.date_creation.isoformat() if v.date_creation else None,
    } for v in veilles])


@veille.route('/api/sources')
@access_required(permission='textes.voir')
@system_admin_required
def api_sources():
    sources = SourceReglementaire.query.order_by(SourceReglementaire.nom).all()
    return jsonify([{
        'id': s.id,
        'nom': s.nom,
        'url': s.url,
        'type_source': s.type_source,
    } for s in sources])


@veille.route('/api/create', methods=['POST'])
@access_required(permission='textes.modifier')
@system_admin_required
def api_create():
    data = request.get_json()
    v = Veille(
        texte_id=data.get('texte_id'),
        source_id=data.get('source_id'),
        date_detection=__import__('datetime').datetime.strptime(data['date_detection'], '%Y-%m-%d').date()
        if data.get('date_detection') else date.today(),
        statut=data.get('statut', 'nouveau'),
        resume=data.get('resume'),
        lien_source=data.get('lien_source'),
    )
    db.session.add(v)
    db.session.commit()
    return jsonify({'success': True, 'id': v.id})


@veille.route('/api/<int:id>/update', methods=['POST'])
@access_required(permission='textes.modifier')
@system_admin_required
def api_update(id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données JSON requises'}), 400
    VeilleResource.update_resource(id)
    return jsonify({'success': True})


@veille.route('/api/<int:id>/delete', methods=['POST'])
@access_required(permission='textes.modifier')
@system_admin_required
def api_delete(id):
    VeilleResource.delete_resource(id)
    return jsonify({'success': True})


@veille.route('/api/source/create', methods=['POST'])
@access_required(permission='textes.modifier')
@system_admin_required
def api_source_create():
    data = request.get_json()
    s = SourceReglementaire(
        nom=data.get('nom'),
        url=data.get('url'),
        type_source=data.get('type_source'),
        contact=data.get('contact'),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'success': True, 'id': s.id})


@veille.route('/api/source/<int:id>/delete', methods=['POST'])
@access_required(permission='textes.modifier')
@system_admin_required
def api_source_delete(id):
    s = SourceReglementaire.query.get_or_404(id)
    Veille.query.filter_by(source_id=id).update({'source_id': None})
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})
