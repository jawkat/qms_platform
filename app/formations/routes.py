from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.formations import blueprint
from app.models.partages import Formation
from app.models.competence import Competence, FormationParticipant, EmployeCompetence
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


@blueprint.route('/api/calendrier')
@login_required
@has_permission('formations.voir')
def api_calendrier():
    domaine = session.get('domaine', 'hse')
    items = Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).all()
    couleurs = {
        'planifiee': '#3b82f6', 'realisee': '#10b981',
        'en_cours': '#f59e0b', 'annulee': '#ef4444',
    }
    return jsonify([{
        'id': r.id,
        'title': r.titre,
        'start': r.date_formation.isoformat() if r.date_formation else None,
        'allDay': True,
        'color': couleurs.get(r.statut, '#6b7280'),
        'extendedProps': {
            'formateur': r.formateur,
            'statut': r.statut,
            'duree': r.duree_heures,
        },
    } for r in items])


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


@blueprint.route('/participants')
@login_required
@has_permission('formations.voir')
def participants():
    formations = Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Formation.date_formation.desc()).all()
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('formations/participants.html',
                           formations=formations, utilisateurs=utilisateurs)


@blueprint.route('/api/participants/<int:formation_id>')
@login_required
@has_permission('formations.voir')
def api_participants_list(formation_id):
    items = FormationParticipant.query.filter_by(formation_id=formation_id).all()
    return jsonify([{
        'id': p.id, 'utilisateur_id': p.utilisateur_id,
        'utilisateur': f'{p.utilisateur.prenom} {p.utilisateur.nom}' if p.utilisateur else '',
        'statut': p.statut, 'evaluation_score': p.evaluation_score,
        'evaluation_commentaire': p.evaluation_commentaire,
        'certifie': p.certifie,
        'date_certification': p.date_certification.isoformat() if p.date_certification else None,
        'date_expiration': p.date_expiration_certification.isoformat() if p.date_expiration_certification else None,
    } for p in items])


@blueprint.route('/api/participants/create', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_participants_create():
    data = request.get_json()
    exists = FormationParticipant.query.filter_by(
        formation_id=data.get('formation_id'),
        utilisateur_id=data.get('utilisateur_id'),
    ).first()
    if exists:
        return jsonify({'success': False, 'error': 'Ce participant est déjà inscrit à cette formation.'}), 400
    p = FormationParticipant(
        formation_id=data['formation_id'],
        utilisateur_id=data['utilisateur_id'],
        statut=data.get('statut', 'inscrit'),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'id': p.id})


@blueprint.route('/api/participants/<int:id>/update', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_participants_update(id):
    p = FormationParticipant.query.get_or_404(id)
    data = request.get_json()
    for f in ('statut', 'evaluation_score', 'evaluation_commentaire', 'certifie'):
        if f in data:
            setattr(p, f, data[f])
    if data.get('date_certification'):
        p.date_certification = datetime.strptime(data['date_certification'], '%Y-%m-%d').date()
    if data.get('date_expiration'):
        p.date_expiration_certification = datetime.strptime(data['date_expiration'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/participants/<int:id>/delete', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_participants_delete(id):
    p = FormationParticipant.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})


# --- Matrice compétences ---

@blueprint.route('/matrice')
@login_required
@has_permission('formations.voir')
def matrice():
    competences = Competence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Competence.nom).all()
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('formations/matrice.html',
                           competences=competences, utilisateurs=utilisateurs)


@blueprint.route('/api/matrice')
@login_required
@has_permission('formations.voir')
def api_matrice():
    items = EmployeCompetence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    return jsonify([{
        'id': e.id, 'utilisateur_id': e.utilisateur_id,
        'utilisateur': f'{e.utilisateur.prenom} {e.utilisateur.nom}' if e.utilisateur else '',
        'competence_id': e.competence_id,
        'competence': e.competence.nom if e.competence else '',
        'niveau_requis': e.niveau_requis,
        'niveau_actuel': e.niveau_actuel,
        'date_evaluation': e.date_evaluation.isoformat() if e.date_evaluation else None,
        'evalue_par_id': e.evalue_par_id,
        'evalue_par': f'{e.evalue_par.prenom} {e.evalue_par.nom}' if e.evalue_par else '',
        'notes': e.notes,
    } for e in items])


@blueprint.route('/api/matrice/create', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_matrice_create():
    data = request.get_json()
    exists = EmployeCompetence.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        utilisateur_id=data['utilisateur_id'],
        competence_id=data['competence_id'],
    ).first()
    if exists:
        return jsonify({'success': False, 'error': 'Cette compétence est déjà évaluée pour cet employé.'}), 400
    e = EmployeCompetence(
        entreprise_id=current_user.entreprise_id,
        utilisateur_id=data['utilisateur_id'],
        competence_id=data['competence_id'],
        niveau_requis=data.get('niveau_requis', 1),
        niveau_actuel=data.get('niveau_actuel', 0),
        date_evaluation=datetime.strptime(data['date_evaluation'], '%Y-%m-%d').date()
        if data.get('date_evaluation') else None,
        evalue_par_id=data.get('evalue_par_id'),
        notes=data.get('notes'),
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'success': True, 'id': e.id})


@blueprint.route('/api/matrice/<int:id>/update', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_matrice_update(id):
    e = EmployeCompetence.query.filter_by(
        id=id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('niveau_requis', 'niveau_actuel', 'evalue_par_id', 'notes'):
        if f in data:
            setattr(e, f, data[f])
    if data.get('date_evaluation'):
        e.date_evaluation = datetime.strptime(data['date_evaluation'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/matrice/<int:id>/delete', methods=['POST'])
@login_required
@has_permission('formations.gerer')
def api_matrice_delete(id):
    e = EmployeCompetence.query.filter_by(
        id=id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return jsonify({'success': True})


# --- Certifications ---

@blueprint.route('/certifications')
@login_required
@has_permission('formations.voir')
def certifications():
    return render_template('formations/certifications.html')
