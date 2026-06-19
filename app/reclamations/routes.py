from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.reclamations import blueprint
from app.models.partages import Reclamation
from app.models.auth import Utilisateur
from datetime import date, datetime


@blueprint.route('/')
@login_required
@module_access_required('reclamations', 'reclamations.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('reclamations/index.html', utilisateurs=utilisateurs)


@blueprint.route('/api/liste')
@login_required
@module_access_required('reclamations', 'reclamations.voir')
def api_liste():
    domaine = session.get('domaine', 'hse')
    items = Reclamation.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Reclamation.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_reclamation': r.date_reclamation.isoformat() if r.date_reclamation else None,
        'client': r.client, 'produit': r.produit, 'lot': r.lot,
        'description': r.description, 'type_reclamation': r.type_reclamation,
        'action': r.action, 'responsable_id': r.responsable_id,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'cloture_le': r.cloture_le.isoformat() if r.cloture_le else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_access_required('reclamations', 'reclamations.gerer')
def api_creer():
    data = request.get_json()
    item = Reclamation(
        entreprise_id=current_user.entreprise_id,
        domaine=session.get('domaine', 'hse'),
        date_reclamation=datetime.strptime(data['date_reclamation'], '%Y-%m-%d').date()
        if data.get('date_reclamation') else date.today(),
        client=data.get('client'), produit=data.get('produit'),
        lot=data.get('lot'), description=data.get('description'),
        type_reclamation=data.get('type_reclamation'),
        action=data.get('action'),
        responsable_id=data.get('responsable_id'),
        statut=data.get('statut', 'ouverte'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_access_required('reclamations', 'reclamations.gerer')
def api_modifier(item_id):
    item = Reclamation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('client', 'produit', 'lot', 'description', 'type_reclamation',
              'action', 'responsable_id', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_reclamation'):
        item.date_reclamation = datetime.strptime(data['date_reclamation'], '%Y-%m-%d').date()
    if data.get('cloture_le'):
        item.cloture_le = datetime.strptime(data['cloture_le'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_access_required('reclamations', 'reclamations.gerer')
def api_supprimer(item_id):
    item = Reclamation.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
