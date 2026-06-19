from flask import render_template, request, jsonify, session
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.fournisseurs import blueprint
from app.models.partages import Fournisseur
from app.models.historique_fournisseur import EvaluationFournisseur, HistoriqueFournisseur
from app.models.auth import Utilisateur
from datetime import datetime, date
from sqlalchemy import func


@blueprint.route('/')
@login_required
@has_permission('fournisseurs.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('fournisseurs/index.html', utilisateurs=utilisateurs)


@blueprint.route('/api/liste')
@login_required
@has_permission('fournisseurs.voir')
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
        'qualification': r.qualification, 'pays': r.pays,
        'delai_livraison': r.delai_livraison, 'taux_defaut': r.taux_defaut,
        'score_qualite': r.score_qualite, 'score_delai': r.score_delai,
        'score_prix': r.score_prix, 'score_global': r.score_global,
        'dernier_audit': r.dernier_audit.isoformat() if r.dernier_audit else None,
        'prochain_audit': r.prochain_audit.isoformat() if r.prochain_audit else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/stats')
@login_required
@has_permission('fournisseurs.voir')
def api_stats():
    eid = current_user.entreprise_id
    base = Fournisseur.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'qualifies': base.filter_by(qualification='qualifie').count(),
        'audits_programmes': base.filter(Fournisseur.prochain_audit.isnot(None)).count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('fournisseurs.gerer')
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
        qualification=data.get('qualification', 'non_qualifie'),
        pays=data.get('pays'), delai_livraison=data.get('delai_livraison'),
        score_qualite=data.get('score_qualite'),
        score_delai=data.get('score_delai'),
        score_prix=data.get('score_prix'),
        dernier_audit=datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
        if data.get('dernier_audit') else None,
        prochain_audit=datetime.strptime(data['prochain_audit'], '%Y-%m-%d').date()
        if data.get('prochain_audit') else None,
        statut=data.get('statut', 'actif'),
    )
    item.calculer_score_global()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('fournisseurs.gerer')
def api_modifier(item_id):
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'contact', 'email', 'telephone', 'produit',
              'certification', 'evaluation', 'statut', 'qualification',
              'pays', 'delai_livraison', 'score_qualite', 'score_delai', 'score_prix'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('produit_fourni') is not None:
        item.produit = data['produit_fourni']
    if data.get('dernier_audit'):
        item.dernier_audit = datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
    if data.get('prochain_audit'):
        item.prochain_audit = datetime.strptime(data['prochain_audit'], '%Y-%m-%d').date()
    item.calculer_score_global()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('fournisseurs.gerer')
def api_supprimer(item_id):
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/evaluer', methods=['POST'])
@login_required
@has_permission('fournisseurs.gerer')
def api_evaluer(item_id):
    item = Fournisseur.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
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
    return jsonify({'success': True})
