from flask import render_template, request, jsonify
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.ishikawa import blueprint
from app.models.ishikawa import AnalyseIshikawa, CauseIshikawa
from datetime import date, datetime


from app.schemas.ishikawa import AnalyseIshikawaSchema, CauseIshikawaSchema


class IshikawaResource(BaseResource):
    model = AnalyseIshikawa
    schema = AnalyseIshikawaSchema
    search_fields = ['description_effet']


@blueprint.route('/')
@access_required(permission='ishikawa.voir')
def index():
    return render_template('ishikawa/index.html')


@blueprint.get('/api/liste')
@access_required(permission='ishikawa.voir')
@blueprint.response(200, AnalyseIshikawaSchema(many=True))
def api_liste():
    """Liste des analyses Ishikawa"""
    return IshikawaResource.list_resources()


@blueprint.post('/api/creer')
@access_required(permission='ishikawa.gerer')
@blueprint.arguments(AnalyseIshikawaSchema)
@blueprint.response(201, AnalyseIshikawaSchema)
def api_creer(data):
    """Créer une nouvelle analyse Ishikawa"""
    data.auteur_id = current_user.id
    
    raw_data = request.get_json()
    for c in raw_data.get('causes', []):
        if c.get('description'):
            data.causes.append(CauseIshikawa(
                categorie=c.get('categorie', 'methode'),
                description=c['description'],
            ))
    return IshikawaResource.create_resource(data)


@blueprint.post('/api/<int:item_id>/modifier')
@access_required(permission='ishikawa.gerer')
@blueprint.arguments(AnalyseIshikawaSchema(partial=True))
@blueprint.response(200, AnalyseIshikawaSchema)
def api_modifier(data, item_id):
    """Modifier une analyse Ishikawa"""
    item = IshikawaResource.get_resource(item_id)
    
    raw_data = request.get_json()
    if 'description_effet' in raw_data:
        item.description_effet = raw_data['description_effet']
    if 'date_analyse' in raw_data:
        item.date_analyse = datetime.strptime(raw_data['date_analyse'], '%Y-%m-%d').date()
        
    if 'causes' in raw_data:
        CauseIshikawa.query.filter_by(analyse_id=item_id).delete()
        for c in raw_data['causes']:
            if c.get('description'):
                item.causes.append(CauseIshikawa(
                    categorie=c.get('categorie', 'methode'),
                    description=c['description'],
                ))
                
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@access_required(permission='ishikawa.gerer')
def api_supprimer(item_id):
    """Supprimer une analyse Ishikawa"""
    return IshikawaResource.delete_resource(item_id)
