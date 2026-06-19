from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models.hse import EPI
from app.hse import blueprint
from datetime import datetime


@blueprint.route('/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def epi_liste():
    return render_template('hse/epi.html')


@blueprint.route('/api/epi')
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi():
    items = EPI.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EPI.date_creation.desc()).all()
    return jsonify([_serialize_epi(r) for r in items])


@blueprint.route('/api/epi/create', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_create():
    data = request.get_json()
    item = EPI(
        entreprise_id=current_user.entreprise_id,
        type_epi=data.get('type_epi', 'autre'),
        designation=data.get('designation', ''),
        marque=data.get('marque'), modele=data.get('modele'),
        numero_serie=data.get('numero_serie'),
        norme_reference=data.get('norme_reference'),
        date_fabrication=datetime.strptime(data['date_fabrication'], '%Y-%m-%d').date() if data.get('date_fabrication') else None,
        date_peremption=datetime.strptime(data['date_peremption'], '%Y-%m-%d').date() if data.get('date_peremption') else None,
        duree_vie_mois=data.get('duree_vie_mois'),
        statut=data.get('statut', 'en_service'),
        utilisateur_affecte_id=data.get('utilisateur_affecte_id'),
        stock_emplacement=data.get('stock_emplacement'),
        prochain_controle=datetime.strptime(data['prochain_controle'], '%Y-%m-%d').date() if data.get('prochain_controle') else None,
        certificat_conformite=data.get('certificat_conformite', False),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/epi/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_update(item_id):
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('type_epi', 'designation', 'marque', 'modele', 'numero_serie',
              'norme_reference', 'duree_vie_mois', 'statut', 'utilisateur_affecte_id',
              'stock_emplacement', 'certificat_conformite'):
        if f in data:
            setattr(item, f, data[f])
    for df in ('date_fabrication', 'date_peremption', 'prochain_controle'):
        if data.get(df):
            setattr(item, df, datetime.strptime(data[df], '%Y-%m-%d').date())
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/epi/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('hse', 'hse.voir_incidents')
def api_epi_delete(item_id):
    item = EPI.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


def _serialize_epi(r):
    return {
        'id': r.id, 'type_epi': r.type_epi, 'designation': r.designation,
        'marque': r.marque, 'modele': r.modele, 'numero_serie': r.numero_serie,
        'norme_reference': r.norme_reference,
        'date_fabrication': r.date_fabrication.isoformat() if r.date_fabrication else None,
        'date_peremption': r.date_peremption.isoformat() if r.date_peremption else None,
        'statut': r.statut,
        'utilisateur_affecte': f'{r.utilisateur_affecte.prenom} {r.utilisateur_affecte.nom}' if r.utilisateur_affecte else '',
        'stock_emplacement': r.stock_emplacement,
        'prochain_controle': r.prochain_controle.isoformat() if r.prochain_controle else None,
        'certificat_conformite': r.certificat_conformite,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    }
