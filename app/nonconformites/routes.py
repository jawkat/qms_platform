from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.entreprise import Entreprise
from app.models.nonconformite import NonConformite
from app.nonconformites import blueprint
from datetime import date, datetime


def _check_access():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise:
        abort(403)


@blueprint.route('/')
@login_required
def index():
    _check_access()
    return render_template('nonconformites/index.html')


@blueprint.route('/api/liste')
@login_required
def api_liste():
    _check_access()
    eid = current_user.entreprise_id
    q = NonConformite.query.filter_by(entreprise_id=eid)

    domaine = request.args.get('domaine')
    if domaine:
        q = q.filter_by(domaine=domaine)

    statut = request.args.get('statut')
    if statut:
        q = q.filter_by(statut=statut)

    gravite = request.args.get('gravite')
    if gravite:
        q = q.filter_by(gravite=gravite)

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                NonConformite.reference.ilike(like),
                NonConformite.description.ilike(like),
            )
        )

    items = q.order_by(NonConformite.date_creation.desc()).all()
    return jsonify([_serialize(r) for r in items])


@blueprint.route('/api/create', methods=['POST'])
@login_required
def api_create():
    _check_access()
    data = request.get_json()
    item = NonConformite(
        entreprise_id=current_user.entreprise_id,
        domaine=data.get('domaine', 'qualite'),
        reference=data.get('reference'),
        date_nc=datetime.strptime(data['date_nc'], '%Y-%m-%d').date() if data.get('date_nc') else date.today(),
        description=data.get('description', ''),
        action_corrective=data.get('action_corrective'),
        responsable_id=data.get('responsable_id'),
        statut=data.get('statut', 'ouverte'),
        gravite=data.get('gravite', 'majeur'),
        produit_processus=data.get('produit_processus'),
        evaluation_id=data.get('evaluation_id'),
        source=data.get('source'),
        cause=data.get('cause'),
        delai=datetime.strptime(data['delai'], '%Y-%m-%d').date() if data.get('delai') else None,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/update', methods=['POST'])
@login_required
def api_update(item_id):
    _check_access()
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('reference', 'description', 'action_corrective', 'responsable_id', 'statut',
              'gravite', 'produit_processus', 'evaluation_id', 'source', 'cause',
              'efficacite_verifiee'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_nc'):
        item.date_nc = datetime.strptime(data['date_nc'], '%Y-%m-%d').date()
    if data.get('delai'):
        item.delai = datetime.strptime(data['delai'], '%Y-%m-%d').date()
    if data.get('cloture_le'):
        item.cloture_le = datetime.strptime(data['cloture_le'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/delete', methods=['POST'])
@login_required
def api_delete(item_id):
    _check_access()
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/valider-cloture', methods=['POST'])
@login_required
def api_valider_cloture(item_id):
    _check_access()
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    item.statut = 'cloturee'
    item.validee_par_id = current_user.id
    item.date_validation_cloture = date.today()
    item.cloture_le = date.today()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/stats')
@login_required
def api_stats():
    _check_access()
    eid = current_user.entreprise_id
    items = NonConformite.query.filter_by(entreprise_id=eid).all()

    stats = {
        'total': len(items),
        'ouvertes': sum(1 for r in items if r.statut == 'ouverte'),
        'en_cours': sum(1 for r in items if r.statut == 'en_cours'),
        'cloturees': sum(1 for r in items if r.statut == 'cloturee'),
        'mineur': sum(1 for r in items if r.gravite == 'mineur'),
        'majeur': sum(1 for r in items if r.gravite == 'majeur'),
        'critique': sum(1 for r in items if r.gravite == 'critique'),
        'hse': sum(1 for r in items if r.domaine == 'hse'),
        'qualite': sum(1 for r in items if r.domaine == 'qualite'),
        'haccp': sum(1 for r in items if r.domaine == 'haccp'),
    }
    return jsonify(stats)


def _serialize(r):
    return {
        'id': r.id, 'domaine': r.domaine,
        'reference': r.reference,
        'date_nc': r.date_nc.isoformat() if r.date_nc else None,
        'description': r.description,
        'action_corrective': r.action_corrective,
        'responsable_id': r.responsable_id,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'statut': r.statut, 'gravite': r.gravite,
        'produit_processus': r.produit_processus,
        'evaluation_id': r.evaluation_id,
        'source': r.source, 'cause': r.cause,
        'delai': r.delai.isoformat() if r.delai else None,
        'cloture_le': r.cloture_le.isoformat() if r.cloture_le else None,
        'efficacite_verifiee': r.efficacite_verifiee,
        'validee_par': f'{r.validee_par.prenom} {r.validee_par.nom}' if r.validee_par else '',
        'date_validation_cloture': r.date_validation_cloture.isoformat() if r.date_validation_cloture else None,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
