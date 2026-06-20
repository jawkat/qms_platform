from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.objectifs import blueprint
from app.models.qualite import ObjectifQualite
from datetime import datetime


@blueprint.route('/')
@login_required
@has_permission('indicateurs.voir')
def index():
    return render_template('objectifs/index.html')


@blueprint.route('/api/liste')
@login_required
@has_permission('indicateurs.voir')
def api_liste():
    items = ObjectifQualite.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ObjectifQualite.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'titre': r.titre, 'description': r.description,
        'indicateur_id': r.indicateur_id, 'cible': r.cible,
        'seuil_alerte': r.seuil_alerte, 'pilote_id': r.pilote_id,
        'date_debut': r.date_debut.isoformat() if r.date_debut else None,
        'date_echeance': r.date_echeance.isoformat() if r.date_echeance else None,
        'statut': r.statut, 'domaine': r.domaine,
        'processus_concerne': r.processus_concerne,
        'progression': r.progression,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('indicateurs.cree')
def api_creer():
    data = request.get_json()
    item = ObjectifQualite(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'), description=data.get('description'),
        indicateur_id=data.get('indicateur_id'),
        cible=data.get('cible'), seuil_alerte=data.get('seuil_alerte'),
        pilote_id=data.get('pilote_id'),
        date_debut=datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
        if data.get('date_debut') else None,
        date_echeance=datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
        if data.get('date_echeance') else None,
        statut=data.get('statut', 'en_cours'),
        domaine=data.get('domaine', 'qualite'),
        processus_concerne=data.get('processus_concerne'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('indicateurs.modifier')
def api_modifier(item_id):
    item = ObjectifQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('titre', 'description', 'indicateur_id', 'cible', 'seuil_alerte',
              'pilote_id', 'statut', 'domaine', 'processus_concerne'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_debut'):
        item.date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
    if data.get('date_echeance'):
        item.date_echeance = datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('indicateurs.modifier')
def api_supprimer(item_id):
    item = ObjectifQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/stats')
@login_required
@has_permission('indicateurs.voir')
def api_stats():
    eid = current_user.entreprise_id
    base = ObjectifQualite.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'atteint': base.filter_by(statut='atteint').count(),
        'en_retard': base.filter_by(statut='en_retard').count(),
        'non_atteint': base.filter_by(statut='non_atteint').count(),
    })
