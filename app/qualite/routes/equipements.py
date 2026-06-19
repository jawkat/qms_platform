from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import Equipement
from app.qualite import blueprint
from datetime import datetime


@blueprint.route('/equipements')
@login_required
@module_access_required('qualite', 'qualite.voir')
def equipements():
    return render_template('qualite/equipements.html')


@blueprint.route('/api/equipements')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_equipements():
    items = Equipement.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Equipement.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'nom': r.nom,
        'modele': r.modele,
        'numero_serie': r.numero_serie,
        'derniere_maintenance': r.derniere_maintenance.isoformat() if r.derniere_maintenance else None,
        'prochaine_maintenance': r.prochaine_maintenance.isoformat() if r.prochaine_maintenance else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/equipements/create', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_equipements_create():
    data = request.get_json()
    item = Equipement(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'),
        modele=data.get('modele'),
        numero_serie=data.get('numero_serie'),
        derniere_maintenance=datetime.strptime(data['derniere_maintenance'], '%Y-%m-%d').date()
        if data.get('derniere_maintenance') else None,
        prochaine_maintenance=datetime.strptime(data['prochaine_maintenance'], '%Y-%m-%d').date()
        if data.get('prochaine_maintenance') else None,
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/equipements/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_equipements_update(item_id):
    item = Equipement.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    item.nom = data.get('nom', item.nom)
    item.modele = data.get('modele', item.modele)
    item.numero_serie = data.get('numero_serie', item.numero_serie)
    if data.get('derniere_maintenance'):
        item.derniere_maintenance = datetime.strptime(data['derniere_maintenance'], '%Y-%m-%d').date()
    if data.get('prochaine_maintenance'):
        item.prochaine_maintenance = datetime.strptime(data['prochaine_maintenance'], '%Y-%m-%d').date()
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/equipements/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_equipements_delete(item_id):
    item = Equipement.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
