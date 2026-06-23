from flask import render_template, request
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.utils.resource_registry import auto_register_crud
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


auto_register_crud(blueprint, NonConformite, NonConformiteSchema,
                   permission_voir='nonconformites.voir', permission_gerer='nonconformites.gerer',
                   flat=True)


@blueprint.route('/')
@access_required(permission='nonconformites.voir')
def index():
    return render_template('nonconformites/index.html')


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
