from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.nonconformites import blueprint
from app.models.nonconformite import NonConformite
from app.schemas.nonconformite import NonConformiteSchema, NonConformiteCreateSchema
from datetime import date


class NonConformiteResource(BaseResource):
    model = NonConformite
    schema = NonConformiteSchema
    filter_fields = {'domaine': 'domaine', 'statut': 'statut', 'gravite': 'gravite'}
    search_fields = ['reference', 'description']


@blueprint.route('/')
@access_required(permission='nonconformites.voir')
def index():
    return render_template('nonconformites/index.html')


@blueprint.get('/api/liste')
@access_required(permission='nonconformites.voir')
@blueprint.response(200, NonConformiteSchema(many=True))
def api_liste():
    """Liste des non-conformités filtrée"""
    return NonConformiteResource.list_resources()


@blueprint.post('/api/creer')
@access_required(permission='nonconformites.gerer')
@blueprint.arguments(NonConformiteCreateSchema)
@blueprint.response(201, NonConformiteSchema)
def api_creer(data):
    """Créer une nouvelle non-conformité"""
    return NonConformiteResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(permission='nonconformites.gerer')
@blueprint.response(200, NonConformiteSchema)
def api_modifier(item_id):
    """Mettre à jour une non-conformité"""
    return NonConformiteResource.update_resource(item_id)


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(permission='nonconformites.gerer')
def api_supprimer(item_id):
    """Supprimer une non-conformité"""
    return NonConformiteResource.delete_resource(item_id)


@blueprint.post('/api/<int:item_id>/valider-cloture')
@access_required(permission='nonconformites.valider_cloture')
@blueprint.response(200, NonConformiteSchema)
def api_valider_cloture(item_id):
    """Valider la clôture d'une non-conformité"""
    item = NonConformiteResource.get_resource(item_id)
    item.statut = 'cloturee'
    item.validee_par_id = current_user.id
    item.date_validation_cloture = date.today()
    item.cloture_le = date.today()
    db.session.commit()
    return item


@blueprint.get('/api/stats')
@access_required(permission='nonconformites.voir')
def api_stats():
    """Statistiques des non-conformités"""
    base = NonConformite.query
    return {
        'total': base.count(),
        'ouvertes': base.filter_by(statut='ouverte').count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'cloturees': base.filter_by(statut='cloturee').count(),
        'mineur': base.filter_by(gravite='mineur').count(),
        'majeur': base.filter_by(gravite='majeur').count(),
        'critique': base.filter_by(gravite='critique').count(),
        'hse': base.filter_by(domaine='hse').count(),
        'qualite': base.filter_by(domaine='qualite').count(),
        'haccp': base.filter_by(domaine='haccp').count(),
    }
