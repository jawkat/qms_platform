from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import ControleQualite
from app.qualite import blueprint
from datetime import date, datetime


@blueprint.route('/controle')
@login_required
@module_access_required('qualite', 'qualite.voir')
def controle():
    return render_template('qualite/controle.html')


@blueprint.route('/api/controle')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_controle():
    items = ControleQualite.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ControleQualite.date_creation.desc()).all()
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
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_controle_create():
    data = request.get_json()
    date_val = datetime.strptime(data['date_controle'], '%Y-%m-%d').date() if data.get('date_controle') else date.today()
    item = ControleQualite(
        entreprise_id=current_user.entreprise_id,
        date_controle=date_val,
        produit=data.get('produit'),
        lot=data.get('lot'),
        type_controle=data.get('type_controle'),
        resultat=data.get('resultat'),
        valeur=data.get('valeur'),
        specification=data.get('specification'),
        inspecteur=data.get('inspecteur'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/controle/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_controle_update(item_id):
    item = ControleQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
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
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_controle_delete(item_id):
    item = ControleQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
