from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.formations import blueprint
from app.models.partages import Formation
from app.models.competence import Competence, FormationParticipant
from app.models.auth import Utilisateur
from datetime import datetime, date
from sqlalchemy import func


@blueprint.route('/')
@login_required
@has_permission('formations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    competences = Competence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Competence.nom).all()
    return render_template('formations/index.html', utilisateurs=utilisateurs, competences=competences)


@blueprint.route('/api/liste')
@login_required
@has_permission('formations.voir')
def api_liste():
    domaine = session.get('domaine', 'hse')
    items = Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Formation.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'titre': r.titre, 'theme': r.theme,
        'formateur': r.formateur, 'participants': r.participants,
        'duree_heures': r.duree_heures,
        'date_formation': r.date_formation.isoformat() if r.date_formation else None,
        'evaluation': r.evaluation, 'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_creer():
    data = request.get_json()
    item = Formation(
        entreprise_id=current_user.entreprise_id,
        domaine=session.get('domaine', 'hse'),
        titre=data.get('titre'), theme=data.get('theme'),
        formateur=data.get('formateur'), participants=data.get('participants'),
        duree_heures=data.get('duree_heures'),
        date_formation=datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
        if data.get('date_formation') else None,
        evaluation=data.get('evaluation'), statut=data.get('statut', 'planifiee'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_modifier(item_id):
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'theme', 'formateur', 'participants', 'duree_heures',
              'evaluation', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_formation'):
        item.date_formation = datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_supprimer(item_id):
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/competences')
@login_required
@has_permission('formations.voir')
def api_competences():
    items = Competence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Competence.nom).all()
    return jsonify([{
        'id': c.id, 'nom': c.nom, 'description': c.description, 'domaine': c.domaine,
    } for c in items])


@blueprint.route('/api/competences/create', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_competences_create():
    data = request.get_json()
    item = Competence(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        domaine=data.get('domaine', 'qualite'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/competences/<int:item_id>/delete', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_competences_delete(item_id):
    item = Competence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/certifications')
@login_required
@has_permission('formations.voir')
def api_certifications():
    items = FormationParticipant.query.join(Formation).filter(
        Formation.entreprise_id == current_user.entreprise_id,
        FormationParticipant.certifie == True,
    ).all()
    result = []
    for fp in items:
        result.append({
            'id': fp.id,
            'utilisateur': f'{fp.utilisateur.prenom} {fp.utilisateur.nom}' if fp.utilisateur else '',
            'utilisateur_id': fp.utilisateur_id,
            'formation': fp.formation.titre if fp.formation else '',
            'date_certification': fp.date_certification.isoformat() if fp.date_certification else None,
            'date_expiration': fp.date_expiration_certification.isoformat() if fp.date_expiration_certification else None,
            'score': fp.evaluation_score,
        })
    return jsonify(result)


@blueprint.route('/api/stats')
@login_required
@has_permission('formations.voir')
def api_stats():
    eid = current_user.entreprise_id
    today = date.today()
    total_formations = Formation.query.filter_by(entreprise_id=eid).count()
    planifiees = Formation.query.filter_by(entreprise_id=eid, statut='planifiee').count()
    realisees = Formation.query.filter_by(entreprise_id=eid, statut='realisee').count()
    certifies = FormationParticipant.query.join(Formation).filter(
        Formation.entreprise_id == eid,
        FormationParticipant.certifie == True,
    ).count()
    expires_bientot = FormationParticipant.query.join(Formation).filter(
        Formation.entreprise_id == eid,
        FormationParticipant.certifie == True,
        FormationParticipant.date_expiration_certification <= today + __import__('datetime').timedelta(days=30),
        FormationParticipant.date_expiration_certification >= today,
    ).count()
    return jsonify({
        'total_formations': total_formations,
        'planifiees': planifiees,
        'realisees': realisees,
        'certifies': certifies,
        'expires_bientot': expires_bientot,
    })
