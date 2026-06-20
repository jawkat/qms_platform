from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.ishikawa import blueprint
from app.models.ishikawa import AnalyseIshikawa, CauseIshikawa
from datetime import date, datetime


@blueprint.route('/')
@login_required
@has_permission('ishikawa.voir')
def index():
    return render_template('ishikawa/index.html')


@blueprint.route('/api/liste')
@login_required
@has_permission('ishikawa.voir')
def api_liste():
    items = AnalyseIshikawa.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(AnalyseIshikawa.date_creation.desc()).all()
    return jsonify([_serialize(r) for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('ishikawa.gerer')
def api_creer():
    data = request.get_json()
    item = AnalyseIshikawa(
        entreprise_id=current_user.entreprise_id,
        source_type=data.get('source_type'),
        source_id=data.get('source_id'),
        description_effet=data.get('description_effet', ''),
        date_analyse=datetime.strptime(data['date_analyse'], '%Y-%m-%d').date() if data.get('date_analyse') else date.today(),
        auteur_id=current_user.id,
    )
    db.session.add(item)
    db.session.flush()
    for c in data.get('causes', []):
        if c.get('description'):
            item.causes.append(CauseIshikawa(
                categorie=c.get('categorie', 'methode'),
                description=c['description'],
            ))
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('ishikawa.gerer')
def api_modifier(item_id):
    item = AnalyseIshikawa.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('description_effet'):
        item.description_effet = data['description_effet']
    if data.get('date_analyse'):
        item.date_analyse = datetime.strptime(data['date_analyse'], '%Y-%m-%d').date()
    if data.get('causes') is not None:
        item.causes.delete()
        for c in data['causes']:
            if c.get('description'):
                item.causes.append(CauseIshikawa(
                    categorie=c.get('categorie', 'methode'),
                    description=c['description'],
                ))
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('ishikawa.gerer')
def api_supprimer(item_id):
    item = AnalyseIshikawa.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


def _serialize(r):
    return {
        'id': r.id, 'source_type': r.source_type, 'source_id': r.source_id,
        'description_effet': r.description_effet,
        'date_analyse': r.date_analyse.isoformat() if r.date_analyse else None,
        'auteur': f'{r.auteur.prenom} {r.auteur.nom}' if r.auteur else '',
        'causes': [{'id': c.id, 'categorie': c.categorie, 'description': c.description} for c in r.causes],
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
