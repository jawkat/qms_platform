from flask import render_template, request, jsonify, session
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.formations import blueprint
from app.models.partages import Formation
from app.models.competence import Competence, FormationParticipant, EmployeCompetence
from app.models.auth import Utilisateur
from datetime import date
from app.schemas.partages import FormationSchema
from app.schemas.competence import CompetenceSchema, FormationParticipantSchema, EmployeCompetenceSchema


# =============================================================================
# Resource definitions
# =============================================================================

class FormationResource(BaseResource):
    model = Formation
    schema = FormationSchema
    search_fields = ['titre', 'formateur', 'theme']


class CompetenceResource(BaseResource):
    model = Competence
    schema = CompetenceSchema
    search_fields = ['nom', 'description']
    sort_field = 'nom'
    sort_dir = 'asc'


class ParticipantResource(BaseResource):
    model = FormationParticipant
    schema = FormationParticipantSchema
    protected_fields = frozenset({'id', 'formation_id', 'utilisateur_id'})
    tenant_field = None


class MatriceResource(BaseResource):
    model = EmployeCompetence
    schema = EmployeCompetenceSchema
    protected_fields = frozenset({'id', 'entreprise_id', 'utilisateur_id', 'competence_id'})
    tenant_field = 'entreprise_id'


# =============================================================================
# Pages HTML
# =============================================================================

@blueprint.route('/')
@access_required(permission='formations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    competences = Competence.query.order_by(Competence.nom).all()
    return render_template('formations/index.html', utilisateurs=utilisateurs, competences=competences)


@blueprint.route('/participants')
@access_required(permission='formations.voir')
def participants():
    formations = Formation.query.order_by(Formation.date_formation.desc()).all()
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('formations/participants.html',
                           formations=formations, utilisateurs=utilisateurs)


@blueprint.route('/matrice')
@access_required(permission='formations.voir')
def matrice():
    competences = Competence.query.order_by(Competence.nom).all()
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('formations/matrice.html',
                           competences=competences, utilisateurs=utilisateurs)


@blueprint.route('/certifications')
@access_required(permission='formations.voir')
def certifications():
    return render_template('formations/certifications.html')


# =============================================================================
# API — Formations CRUD
# =============================================================================

@blueprint.get('/api/liste')
@access_required(permission='formations.voir')
@blueprint.response(200, FormationSchema(many=True))
def api_liste():
    """Liste des formations (filtrée par domaine depuis la session)"""
    domaine = session.get('domaine', 'hse')
    return Formation.query.filter_by(
        domaine=domaine
    ).order_by(Formation.date_creation.desc()).all()


@blueprint.post('/api/creer')
@access_required(permission='formations.gerer')
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
@access_required(permission='formations.gerer')
@blueprint.arguments(FormationSchema(partial=True))
@blueprint.response(200, FormationSchema)
def api_modifier(data, item_id):
    """Mettre à jour une formation"""
    return FormationResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(permission='formations.gerer')
def api_supprimer(item_id):
    """Supprimer une formation"""
    return FormationResource.delete_resource(item_id)


# =============================================================================
# API — Compétences
# =============================================================================

@blueprint.get('/api/competences')
@access_required(permission='formations.voir')
@blueprint.response(200, CompetenceSchema(many=True))
def api_competences():
    """Liste des compétences"""
    return Competence.query.order_by(Competence.nom).all()


@blueprint.post('/api/competences/create')
@access_required(permission='formations.gerer')
@blueprint.arguments(CompetenceSchema)
@blueprint.response(201, CompetenceSchema)
def api_competences_create(data):
    """Créer une nouvelle compétence"""
    return CompetenceResource.create_resource(data)


@blueprint.post('/api/competences/<int:item_id>/delete')
@access_required(permission='formations.gerer')
def api_competences_delete(item_id):
    """Supprimer une compétence"""
    return CompetenceResource.delete_resource(item_id)


# =============================================================================
# API — Certifications
# =============================================================================

@blueprint.get('/api/certifications')
@access_required(permission='formations.voir')
@blueprint.response(200, FormationParticipantSchema(many=True))
def api_certifications():
    """Liste des participants certifiés"""
    return FormationParticipant.query.join(Formation).filter(
        FormationParticipant.certifie == True).all()


# =============================================================================
# API — Calendrier & Stats
# =============================================================================

@blueprint.get('/api/calendrier')
@access_required(permission='formations.voir')
def api_calendrier():
    """Calendrier des formations"""
    domaine = session.get('domaine', 'hse')
    items = Formation.query.filter_by(
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
@access_required(permission='formations.voir')
def api_stats():
    """Statistiques formations"""
    today = date.today()
    total_formations = Formation.query.count()
    planifiees = Formation.query.filter_by(statut='planifiee').count()
    realisees = Formation.query.filter_by(statut='realisee').count()
    certifies = FormationParticipant.query.join(Formation).filter(
        FormationParticipant.certifie == True).count()
    expires_bientot = FormationParticipant.query.join(Formation).filter(
        FormationParticipant.certifie == True,
        FormationParticipant.date_expiration_certification <= today + __import__('datetime').timedelta(days=30),
        FormationParticipant.date_expiration_certification >= today).count()
    return {
        'total_formations': total_formations,
        'planifiees': planifiees,
        'realisees': realisees,
        'certifies': certifies,
        'expires_bientot': expires_bientot,
    }


# =============================================================================
# API — Participants
# =============================================================================

@blueprint.get('/api/participants/<int:formation_id>')
@access_required(permission='formations.voir')
@blueprint.response(200, FormationParticipantSchema(many=True))
def api_participants_list(formation_id):
    """Liste des participants à une formation"""
    return FormationParticipant.query.filter_by(formation_id=formation_id).all()


@blueprint.post('/api/participants/create')
@access_required(permission='formations.gerer')
@blueprint.arguments(FormationParticipantSchema)
@blueprint.response(201, FormationParticipantSchema)
def api_participants_create(data):
    """Inscrire un participant à une formation"""
    exists = FormationParticipant.query.filter_by(
        formation_id=data.formation_id,
        utilisateur_id=data.utilisateur_id).first()
    if exists:
        return jsonify({"message": "Ce participant est déjà inscrit à cette formation."}), 400
    return ParticipantResource.create_resource(data)


@blueprint.post('/api/participants/<int:id>/update')
@access_required(permission='formations.gerer')
@blueprint.arguments(FormationParticipantSchema(partial=True))
@blueprint.response(200, FormationParticipantSchema)
def api_participants_update(data, id):
    """Mettre à jour un participant"""
    return ParticipantResource.update_resource(id)


@blueprint.post('/api/participants/<int:id>/delete')
@access_required(permission='formations.gerer')
def api_participants_delete(id):
    """Supprimer un participant"""
    return ParticipantResource.delete_resource(id)


# =============================================================================
# API — Matrice Compétences
# =============================================================================

@blueprint.get('/api/matrice')
@access_required(permission='formations.voir')
@blueprint.response(200, EmployeCompetenceSchema(many=True))
def api_matrice():
    """Matrice des compétences des employés"""
    return EmployeCompetence.query.all()


@blueprint.post('/api/matrice/create')
@access_required(permission='formations.gerer')
@blueprint.arguments(EmployeCompetenceSchema)
@blueprint.response(201, EmployeCompetenceSchema)
def api_matrice_create(data):
    """Évaluer une compétence pour un employé"""
    exists = EmployeCompetence.query.filter_by(
        utilisateur_id=data.utilisateur_id,
        competence_id=data.competence_id).first()
    if exists:
        return jsonify({"message": "Cette compétence est déjà évaluée pour cet employé."}), 400
    return MatriceResource.create_resource(data)


@blueprint.post('/api/matrice/<int:id>/update')
@access_required(permission='formations.gerer')
@blueprint.arguments(EmployeCompetenceSchema(partial=True))
@blueprint.response(200, EmployeCompetenceSchema)
def api_matrice_update(data, id):
    """Mettre à jour une évaluation de compétence"""
    return MatriceResource.update_resource(id)


@blueprint.post('/api/matrice/<int:id>/delete')
@access_required(permission='formations.gerer')
def api_matrice_delete(id):
    """Supprimer une évaluation de compétence"""
    return MatriceResource.delete_resource(id)
