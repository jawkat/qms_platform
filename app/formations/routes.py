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
from app.schemas.partages import FormationSchema
from app.schemas.competence import CompetenceSchema, FormationParticipantSchema, EmployeCompetenceSchema


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


@blueprint.get('/api/liste')
@login_required
@has_permission('formations.voir')
@blueprint.response(200, FormationSchema(many=True))
def api_liste():
    """Liste des formations"""
    domaine = session.get('domaine', 'hse')
    return Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Formation.date_creation.desc()).all()


@blueprint.post('/api/creer')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(FormationSchema)
@blueprint.response(201, FormationSchema)
def api_creer(data):
    """Créer une nouvelle formation"""
    data.entreprise_id = current_user.entreprise_id
    data.domaine = session.get('domaine', 'hse')
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(FormationSchema(partial=True))
@blueprint.response(200, FormationSchema)
def api_modifier(data, item_id):
    """Mettre à jour une formation"""
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('formations.gerer')
def api_supprimer(item_id):
    """Supprimer une formation"""
    item = Formation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.get('/api/competences')
@login_required
@has_permission('formations.voir')
@blueprint.response(200, CompetenceSchema(many=True))
def api_competences():
    """Liste des compétences"""
    return Competence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Competence.nom).all()


@blueprint.post('/api/competences/create')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(CompetenceSchema)
@blueprint.response(201, CompetenceSchema)
def api_competences_create(data):
    """Créer une nouvelle compétence"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/competences/<int:item_id>/delete')
@login_required
@has_permission('formations.gerer')
def api_competences_delete(item_id):
    """Supprimer une compétence"""
    item = Competence.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.get('/api/certifications')
@login_required
@has_permission('formations.voir')
@blueprint.response(200, FormationParticipantSchema(many=True))
def api_certifications():
    """Liste des participants certifiés"""
    return FormationParticipant.query.join(Formation).filter(
        Formation.entreprise_id == current_user.entreprise_id,
        FormationParticipant.certifie == True,
    ).all()


@blueprint.get('/api/calendrier')
@login_required
@has_permission('formations.voir')
def api_calendrier():
    """Calendrier des formations"""
    domaine = session.get('domaine', 'hse')
    items = Formation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).all()
    couleurs = {
        'planifiee': '#3b82f6', 'realisee': '#10b981',
        'en_cours': '#f59e0b', 'annulee': '#ef4444',
    }
    return [{
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
    } for r in items]


@blueprint.get('/api/stats')
@login_required
@has_permission('formations.voir')
def api_stats():
    """Statistiques formations"""
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
    return {
        'total_formations': total_formations,
        'planifiees': planifiees,
        'realisees': realisees,
        'certifies': certifies,
        'expires_bientot': expires_bientot,
    }


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


@blueprint.get('/api/participants/<int:formation_id>')
@login_required
@has_permission('formations.voir')
@blueprint.response(200, FormationParticipantSchema(many=True))
def api_participants_list(formation_id):
    """Liste des participants à une formation"""
    return FormationParticipant.query.filter_by(formation_id=formation_id).all()


@blueprint.post('/api/participants/create')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(FormationParticipantSchema)
@blueprint.response(201, FormationParticipantSchema)
def api_participants_create(data):
    """Inscrire un participant à une formation"""
    exists = FormationParticipant.query.filter_by(
        formation_id=data.formation_id,
        utilisateur_id=data.utilisateur_id,
    ).first()
    if exists:
        return {"message": "Ce participant est déjà inscrit à cette formation."}, 400
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/participants/<int:id>/update')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(FormationParticipantSchema(partial=True))
@blueprint.response(200, FormationParticipantSchema)
def api_participants_update(data, id):
    """Mettre à jour un participant"""
    p = FormationParticipant.query.get_or_404(id)
    for field, value in request.get_json().items():
        if hasattr(p, field) and field not in ('id', 'formation_id', 'utilisateur_id'):
            setattr(p, field, value)
    db.session.commit()
    return p


@blueprint.post('/api/participants/<int:id>/delete')
@login_required
@has_permission('formations.gerer')
def api_participants_delete(id):
    """Supprimer un participant"""
    p = FormationParticipant.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return {'success': True}


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


@blueprint.get('/api/matrice')
@login_required
@has_permission('formations.voir')
@blueprint.response(200, EmployeCompetenceSchema(many=True))
def api_matrice():
    """Matrice des compétences des employés"""
    return EmployeCompetence.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()


@blueprint.post('/api/matrice/create')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(EmployeCompetenceSchema)
@blueprint.response(201, EmployeCompetenceSchema)
def api_matrice_create(data):
    """Évaluer une compétence pour un employé"""
    exists = EmployeCompetence.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        utilisateur_id=data.utilisateur_id,
        competence_id=data.competence_id,
    ).first()
    if exists:
        return {"message": "Cette compétence est déjà évaluée pour cet employé."}, 400
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/matrice/<int:id>/update')
@login_required
@has_permission('formations.gerer')
@blueprint.arguments(EmployeCompetenceSchema(partial=True))
@blueprint.response(200, EmployeCompetenceSchema)
def api_matrice_update(data, id):
    """Mettre à jour une évaluation de compétence"""
    e = EmployeCompetence.query.filter_by(
        id=id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(e, field) and field not in ('id', 'entreprise_id', 'utilisateur_id', 'competence_id'):
            setattr(e, field, value)
    db.session.commit()
    return e


@blueprint.post('/api/matrice/<int:id>/delete')
@login_required
@has_permission('formations.gerer')
def api_matrice_delete(id):
    """Supprimer une évaluation de compétence"""
    e = EmployeCompetence.query.filter_by(
        id=id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return {'success': True}


# --- Certifications ---

@blueprint.route('/certifications')
@login_required
@has_permission('formations.voir')
def certifications():
    return render_template('formations/certifications.html')
