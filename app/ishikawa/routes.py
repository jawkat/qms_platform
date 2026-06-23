from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.ishikawa import blueprint
from app.models.ishikawa import AnalyseIshikawa, CauseIshikawa
from datetime import date, datetime


from app.schemas.ishikawa import AnalyseIshikawaSchema, CauseIshikawaSchema


@blueprint.route('/')
@login_required
@has_permission('ishikawa.voir')
def index():
    return render_template('ishikawa/index.html')


@blueprint.get('/api/liste')
@login_required
@has_permission('ishikawa.voir')
@blueprint.response(200, AnalyseIshikawaSchema(many=True))
def api_liste():
    """Liste des analyses Ishikawa"""
    return AnalyseIshikawa.query.order_by(AnalyseIshikawa.date_creation.desc()).all()


@blueprint.post('/api/creer')
@login_required
@has_permission('ishikawa.gerer')
@blueprint.arguments(AnalyseIshikawaSchema)
@blueprint.response(201, AnalyseIshikawaSchema)
def api_creer(data):
    """Créer une nouvelle analyse Ishikawa"""
    data.entreprise_id = current_user.entreprise_id
    data.auteur_id = current_user.id
    
    # Extra handling for causes if they are passed in JSON
    raw_data = request.get_json()
    for c in raw_data.get('causes', []):
        if c.get('description'):
            data.causes.append(CauseIshikawa(
                categorie=c.get('categorie', 'methode'),
                description=c['description'],
            ))
            
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('ishikawa.gerer')
@blueprint.arguments(AnalyseIshikawaSchema(partial=True))
@blueprint.response(200, AnalyseIshikawaSchema)
def api_modifier(data, item_id):
    """Modifier une analyse Ishikawa"""
    item = AnalyseIshikawa.query.filter_by(
        id=item_id
    ).first_or_404()
    
    raw_data = request.get_json()
    if 'description_effet' in raw_data:
        item.description_effet = raw_data['description_effet']
    if 'date_analyse' in raw_data:
        item.date_analyse = datetime.strptime(raw_data['date_analyse'], '%Y-%m-%d').date()
        
    if 'causes' in raw_data:
        # Clear existing causes and replace
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
@login_required
@has_permission('ishikawa.gerer')
def api_supprimer(item_id):
    """Supprimer une analyse Ishikawa"""
    item = AnalyseIshikawa.query.filter_by(
        id=item_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
