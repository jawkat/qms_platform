"""Routes du module Laboratoire."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

blueprint = Blueprint('laboratoire', __name__, template_folder='templates')


@blueprint.route('/')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
def index():
    return render_template('laboratoire/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
def api_liste():
    from app.laboratoire.models import PlanAnalyse
    items = PlanAnalyse.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(PlanAnalyse.nom).all()
    return jsonify([{
        'id': i.id, 'nom': i.nom, 'description': i.description,
        'produit_concerne': i.produit_concerne, 'parametre': i.parametre,
        'methode': i.methode, 'frequence': i.frequence,
        'seuil_min': i.seuil_min, 'seuil_max': i.seuil_max,
        'unite': i.unite, 'statut': i.statut,
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.voir')
def api_stats():
    from app.laboratoire.models import PlanAnalyse, Echantillon, ResultatAnalyse
    eid = current_user.entreprise_id
    return jsonify({
        'plans': PlanAnalyse.query.filter_by(entreprise_id=eid).count(),
        'echantillons': Echantillon.query.filter_by(entreprise_id=eid).count(),
        'resultats': ResultatAnalyse.query.filter_by(entreprise_id=eid).count(),
        'non_conformes': ResultatAnalyse.query.filter_by(entreprise_id=eid, conforme=False).count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
def api_creer():
    from app.laboratoire.models import PlanAnalyse
    data = request.get_json()
    item = PlanAnalyse(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), description=data.get('description'),
        produit_concerne=data.get('produit_concerne'),
        parametre=data.get('parametre'), methode=data.get('methode'),
        frequence=data.get('frequence'),
        seuil_min=data.get('seuil_min'), seuil_max=data.get('seuil_max'),
        unite=data.get('unite'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
def api_modifier(item_id):
    from app.laboratoire.models import PlanAnalyse
    item = PlanAnalyse.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('nom', 'description', 'produit_concerne', 'parametre', 'methode', 'frequence', 'seuil_min', 'seuil_max', 'unite', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('laboratoire')
@has_permission('laboratoire.gerer')
def api_supprimer(item_id):
    from app.laboratoire.models import PlanAnalyse
    item = PlanAnalyse.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
