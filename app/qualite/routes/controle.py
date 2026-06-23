from flask import render_template, request, jsonify
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models import ControleQualite
from app.qualite import blueprint
from app.schemas.qualite import ControleQualiteSchema
from datetime import date, datetime


class ControleQualiteResource(BaseResource):
    model = ControleQualite
    schema = ControleQualiteSchema
    search_fields = ['produit', 'lot', 'type_controle', 'inspecteur']
    filter_fields = {'resultat': 'resultat', 'type_controle': 'type_controle'}


@blueprint.route('/controle')
@access_required(module='qualite', permission='qualite.voir')
def controle():
    return render_template('qualite/controle.html')


@blueprint.route('/api/controle')
@access_required(module='qualite', permission='qualite.voir')
def api_controle():
    items = ControleQualiteResource.list_resources()
    return jsonify([{
        'id': r.id,
        'date_controle': r.date_controle.isoformat() if r.date_controle else None,
        'produit': r.produit,
        'lot': r.lot,
        'type_controle': r.type_controle,
        'resultat': r.resultat,
        'valeur': r.valeur,
        'specification': r.specification,
        'inspecteur': r.inspecteur,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/controle/create', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_controle_create():
    data = request.get_json()
    date_val = datetime.strptime(data['date_controle'], '%Y-%m-%d').date() if data.get('date_controle') else date.today()
    item = ControleQualite(
        date_controle=date_val,
        produit=data.get('produit'),
        lot=data.get('lot'),
        type_controle=data.get('type_controle'),
        resultat=data.get('resultat'),
        valeur=data.get('valeur'),
        specification=data.get('specification'),
        inspecteur=data.get('inspecteur'),
    )
    ControleQualiteResource.create_resource(item)
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/controle/<int:item_id>/update', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_controle_update(item_id):
    item = ControleQualiteResource.get_resource(item_id)
    data = request.get_json()
    if data.get('date_controle'):
        item.date_controle = datetime.strptime(data['date_controle'], '%Y-%m-%d').date()
    item.produit = data.get('produit', item.produit)
    item.lot = data.get('lot', item.lot)
    item.type_controle = data.get('type_controle', item.type_controle)
    item.resultat = data.get('resultat', item.resultat)
    item.valeur = data.get('valeur', item.valeur)
    item.specification = data.get('specification', item.specification)
    item.inspecteur = data.get('inspecteur', item.inspecteur)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/controle/<int:item_id>/delete', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_controle_delete(item_id):
    ControleQualiteResource.delete_resource(item_id)
    return jsonify({'success': True})
