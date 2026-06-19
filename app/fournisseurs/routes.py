from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.fournisseurs import blueprint
from app.models.partages import Fournisseur
from datetime import datetime


@blueprint.route('/')
@login_required
@module_access_required('fournisseurs', 'fournisseurs.voir')
def index():
    return render_template('fournisseurs/index.html')


@blueprint.route('/api/liste')
@login_required
@module_access_required('fournisseurs', 'fournisseurs.voir')
def api_liste():
    domaine = session.get('domaine', 'hse')
    items = Fournisseur.query.filter_by(
        entreprise_id=current_user.entreprise_id,
        domaine=domaine
    ).order_by(Fournisseur.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'nom': r.nom, 'contact': r.contact, 'email': r.email,
        'telephone': r.telephone, 'produit_fourni': r.produit_fourni,
        'certification': r.certification, 'evaluation': r.evaluation,
        'dernier_audit': r.dernier_audit.isoformat() if r.dernier_audit else None,
        'prochain_audit': r.prochain_audit.isoformat() if r.prochain_audit else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_access_required('fournisseurs', 'fournisseurs.gerer')
def api_creer():
    data = request.get_json()
    item = Fournisseur(
        entreprise_id=current_user.entreprise_id,
        domaine=session.get('domaine', 'hse'),
        nom=data.get('nom'), contact=data.get('contact'),
        email=data.get('email'), telephone=data.get('telephone'),
        produit=data.get('produit_fourni'),
        certification=data.get('certification'),
        evaluation=data.get('evaluation'),
        dernier_audit=datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
        if data.get('dernier_audit') else None,
        prochain_audit=datetime.strptime(data['prochain_audit'], '%Y-%m-%d').date()
        if data.get('prochain_audit') else None,
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_access_required('fournisseurs', 'fournisseurs.gerer')
def api_modifier(item_id):
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'contact', 'email', 'telephone', 'produit',
              'certification', 'evaluation', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('produit_fourni') is not None:
        item.produit = data['produit_fourni']
    if data.get('dernier_audit'):
        item.dernier_audit = datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
    if data.get('prochain_audit'):
        item.prochain_audit = datetime.strptime(data['prochain_audit'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_access_required('fournisseurs', 'fournisseurs.gerer')
def api_supprimer(item_id):
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
