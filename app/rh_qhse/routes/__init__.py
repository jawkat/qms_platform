"""Routes du module RH QHSE."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app.core import module_active
from app import db

blueprint = Blueprint('rh_qhse', __name__, template_folder='templates')


@blueprint.route('/')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
def index():
    return render_template('rh_qhse/index.html')


@blueprint.route('/api/liste')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
def api_liste():
    from app.rh_qhse.models import EmployeQHSE
    items = EmployeQHSE.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).all()
    return jsonify([{
        'id': i.id, 'matricule': i.matricule, 'poste': i.poste,
        'department': i.department, 'statut': i.statut,
        'date_embauche': i.date_embauche.isoformat() if i.date_embauche else None,
        'date_visite_medicale': i.date_visite_medicale.isoformat() if i.date_visite_medicale else None,
        'date_prochaine_visite': i.date_prochaine_visite.isoformat() if i.date_prochaine_visite else None,
        'utilisateur': f'{i.utilisateur.prenom} {i.utilisateur.nom}' if i.utilisateur else '',
    } for i in items])


@blueprint.route('/api/stats')
@login_required
@module_active('rh_qhse')
@has_permission('rh.voir')
def api_stats():
    from app.rh_qhse.models import EmployeQHSE
    from datetime import date, timedelta
    eid = current_user.entreprise_id
    base = EmployeQHSE.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'actifs': base.filter_by(statut='actif').count(),
        'visites_a_faire': base.filter(EmployeQHSE.date_prochaine_visite <= date.today()).count() if base.filter(EmployeQHSE.date_prochaine_visite.isnot(None)).count() else 0,
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
def api_creer():
    from app.rh_qhse.models import EmployeQHSE
    from datetime import datetime
    data = request.get_json()
    item = EmployeQHSE(
        entreprise_id=current_user.entreprise_id,
        utilisateur_id=data.get('utilisateur_id'),
        matricule=data.get('matricule'), poste=data.get('poste'),
        department=data.get('department'),
    )
    if data.get('date_embauche'):
        item.date_embauche = datetime.strptime(data['date_embauche'], '%Y-%m-%d').date()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
def api_modifier(item_id):
    from app.rh_qhse.models import EmployeQHSE
    from datetime import datetime
    item = EmployeQHSE.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('matricule', 'poste', 'department', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_visite_medicale'):
        item.date_visite_medicale = datetime.strptime(data['date_visite_medicale'], '%Y-%m-%d').date()
    if data.get('date_prochaine_visite'):
        item.date_prochaine_visite = datetime.strptime(data['date_prochaine_visite'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@module_active('rh_qhse')
@has_permission('rh.gerer')
def api_supprimer(item_id):
    from app.rh_qhse.models import EmployeQHSE
    item = EmployeQHSE.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
