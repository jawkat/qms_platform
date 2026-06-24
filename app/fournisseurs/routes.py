from flask import render_template, request, jsonify, session
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
from app.services.fournisseur_service import FournisseurService
from app import db
from app.fournisseurs import blueprint
from app.models.partages import Fournisseur
from app.models.historique_fournisseur import EvaluationFournisseur, HistoriqueFournisseur
from app.models.auth import Utilisateur
from datetime import datetime, date
from sqlalchemy import func


from app.schemas.partages import FournisseurSchema


class FournisseurResource(BaseResource):
    model = Fournisseur
    schema = FournisseurSchema
    service_class = FournisseurService
    search_fields = ['nom', 'contact', 'produit']

    @classmethod
    def create_resource(cls, data):
        data.entreprise_id = current_user.entreprise_id
        return super().create_resource(data)


auto_register_crud(blueprint, Fournisseur, FournisseurSchema,
                   permission_voir='fournisseurs.voir', permission_gerer='fournisseurs.gerer',
                   flat=True)


@blueprint.route('/')
@access_required(permission='fournisseurs.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('fournisseurs/index.html', utilisateurs=utilisateurs)


@blueprint.get('/api/stats')
@access_required(permission='fournisseurs.voir')
def api_stats():
    """Statistiques fournisseurs"""
    base = Fournisseur.query
    return {
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'qualifies': base.filter_by(qualification='qualifie').count(),
        'audits_programmes': base.filter(Fournisseur.prochain_audit.isnot(None)).count(),
    }


@blueprint.post('/api/<int:item_id>/evaluer')
@access_required(permission='fournisseurs.gerer')
def api_evaluer(item_id):
    """Enregistrer une évaluation périodique"""
    item = FournisseurResource.get_resource(item_id)
    data = request.get_json()
    evaluation = EvaluationFournisseur(
        fournisseur_id=item_id,
        date_evaluation=date.today(),
        evaluateur_id=current_user.id,
        score_global=item.score_global,
        commentaire=data.get('commentaire'),
    )
    db.session.add(evaluation)

    historique = HistoriqueFournisseur(
        fournisseur_id=item_id,
        type_evenement='evaluation',
        date_evenement=date.today(),
        description=f'Évaluation score: {item.score_global}',
        score=item.score_global,
        auteur_id=current_user.id,
    )
    db.session.add(historique)
    db.session.commit()
    return {'success': True}
