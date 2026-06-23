from flask import render_template, request, jsonify, redirect, url_for
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app import db
from app.models.qualite import Equipement, EnregistrementEtalonnage
from app.qualite import blueprint
from app.schemas.qualite import EquipementSchema, EnregistrementEtalonnageSchema
from datetime import datetime


class EquipementResource(BaseResource):
    model = Equipement
    schema = EquipementSchema
    search_fields = ['nom', 'modele', 'numero_serie']
    filter_fields = {'statut': 'statut', 'type_equipement': 'type_equipement', 'statut_metrologique': 'statut_metrologique'}


class EnregistrementEtalonnageResource(BaseResource):
    model = EnregistrementEtalonnage
    schema = EnregistrementEtalonnageSchema
    search_fields = ['operateur', 'certificat_id', 'notes']


@blueprint.route('/equipements')
@access_required(module='qualite', permission='qualite.voir')
def equipements():
    return render_template('qualite/equipements.html')


@blueprint.route('/api/equipements')
@access_required(module='qualite', permission='qualite.voir')
def api_equipements():
    items = EquipementResource.list_resources()
    return jsonify([{
        'id': r.id,
        'nom': r.nom,
        'modele': r.modele,
        'numero_serie': r.numero_serie,
        'type_equipement': r.type_equipement,
        'derniere_maintenance': r.derniere_maintenance.isoformat() if r.derniere_maintenance else None,
        'prochaine_maintenance': r.prochaine_maintenance.isoformat() if r.prochaine_maintenance else None,
        'frequence_etalonnage_jours': r.frequence_etalonnage_jours,
        'precision': r.precision,
        'unite_mesure': r.unite_mesure,
        'tolerance_min': r.tolerance_min,
        'tolerance_max': r.tolerance_max,
        'date_dernier_etalonnage': r.date_dernier_etalonnage.isoformat() if r.date_dernier_etalonnage else None,
        'date_prochain_etalonnage': r.date_prochain_etalonnage.isoformat() if r.date_prochain_etalonnage else None,
        'organisme_etalonnage': r.organisme_etalonnage,
        'certificat_etalonnage': r.certificat_etalonnage,
        'statut_metrologique': r.statut_metrologique,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/equipements/create', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_equipements_create():
    data = request.get_json()
    item = Equipement(
        nom=data.get('nom'),
        modele=data.get('modele'),
        numero_serie=data.get('numero_serie'),
        type_equipement=data.get('type_equipement', 'production'),
        derniere_maintenance=datetime.strptime(data['derniere_maintenance'], '%Y-%m-%d').date()
        if data.get('derniere_maintenance') else None,
        prochaine_maintenance=datetime.strptime(data['prochaine_maintenance'], '%Y-%m-%d').date()
        if data.get('prochaine_maintenance') else None,
        frequence_etalonnage_jours=data.get('frequence_etalonnage_jours'),
        precision=data.get('precision'),
        unite_mesure=data.get('unite_mesure'),
        tolerance_min=data.get('tolerance_min'),
        tolerance_max=data.get('tolerance_max'),
        date_dernier_etalonnage=datetime.strptime(data['date_dernier_etalonnage'], '%Y-%m-%d').date()
        if data.get('date_dernier_etalonnage') else None,
        date_prochain_etalonnage=datetime.strptime(data['date_prochain_etalonnage'], '%Y-%m-%d').date()
        if data.get('date_prochain_etalonnage') else None,
        organisme_etalonnage=data.get('organisme_etalonnage'),
        certificat_etalonnage=data.get('certificat_etalonnage'),
        statut_metrologique=data.get('statut_metrologique', 'en_cours'),
        statut=data.get('statut', 'actif'),
    )
    EquipementResource.create_resource(item)
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/equipements/<int:item_id>/update', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_equipements_update(item_id):
    item = EquipementResource.get_resource(item_id)
    data = request.get_json()
    for f in ('nom', 'modele', 'numero_serie', 'type_equipement', 'statut',
              'precision', 'unite_mesure', 'organisme_etalonnage', 'certificat_etalonnage',
              'statut_metrologique', 'frequence_etalonnage_jours',
              'tolerance_min', 'tolerance_max'):
        if f in data:
            setattr(item, f, data[f])
    for d in ('derniere_maintenance', 'prochaine_maintenance', 'date_dernier_etalonnage', 'date_prochain_etalonnage'):
        if data.get(d):
            setattr(item, d, datetime.strptime(data[d], '%Y-%m-%d').date())
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/equipements/<int:item_id>/delete', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_equipements_delete(item_id):
    EquipementResource.delete_resource(item_id)
    return jsonify({'success': True})


# --- Métrologie : Enregistrements d'étalonnage ---

@blueprint.route('/api/etalonnages/<int:equipement_id>')
@access_required(module='qualite', permission='qualite.voir')
def api_etalonnages(equipement_id):
    items = EnregistrementEtalonnage.query.filter_by(
        equipement_id=equipement_id).order_by(EnregistrementEtalonnage.date_etalonnage.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_etalonnage': r.date_etalonnage.isoformat() if r.date_etalonnage else None,
        'valeur_mesuree': r.valeur_mesuree,
        'valeur_reference': r.valeur_reference,
        'ecart': r.ecart,
        'conforme': r.conforme,
        'certificat_id': r.certificat_id,
        'operateur': r.operateur,
        'notes': r.notes,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/etalonnages/create', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_etalonnages_create():
    data = request.get_json()
    ecart = None
    if data.get('valeur_mesuree') is not None and data.get('valeur_reference') is not None:
        ecart = data['valeur_mesuree'] - data['valeur_reference']
    item = EnregistrementEtalonnage(
        entreprise_id=current_user.entreprise_id,
        equipement_id=data['equipement_id'],
        date_etalonnage=datetime.strptime(data['date_etalonnage'], '%Y-%m-%d').date(),
        valeur_mesuree=data.get('valeur_mesuree'),
        valeur_reference=data.get('valeur_reference'),
        ecart=ecart,
        conforme=data.get('conforme', True),
        certificat_id=data.get('certificat_id'),
        operateur=data.get('operateur'),
        notes=data.get('notes'),
    )
    db.session.add(item)
    # Mettre à jour les dates d'étalonnage sur l'équipement
    eq = db.session.get(Equipement, data['equipement_id'])
    if eq:
        eq.date_dernier_etalonnage = item.date_etalonnage
        if eq.frequence_etalonnage_jours:
            from datetime import timedelta
            eq.date_prochain_etalonnage = item.date_etalonnage + timedelta(days=eq.frequence_etalonnage_jours)
        eq.statut_metrologique = 'etalonne' if item.conforme else 'en_cours'
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/etalonnages/<int:item_id>/delete', methods=['POST'])
@access_required(module='qualite', permission='qualite.voir')
def api_etalonnages_delete(item_id):
    EnregistrementEtalonnageResource.delete_resource(item_id)
    return jsonify({'success': True})
