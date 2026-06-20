from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.haccp import blueprint
from app.haccp.models import (
    ProcessusHaccp, ProduitHaccp, AnalyseDanger, Ccp,
    EnregistrementCcp, Prp, EnregistrementOprp,
    TracabiliteLot, RappelProduit,
)
from app.models.nonconformite import NonConformite
from datetime import date, datetime




# --- Pages ---

@blueprint.route('/')
@login_required
@module_access_required('haccp', 'haccp.voir')
def tableau_de_bord():
    return render_template('haccp/tableau_de_bord.html')


@blueprint.route('/processus')
@login_required
@module_access_required('haccp', 'haccp.voir')
def processus():
    return render_template('haccp/processus.html')


@blueprint.route('/produits')
@login_required
@module_access_required('haccp', 'haccp.voir')
def produits():
    return render_template('haccp/produits.html')


@blueprint.route('/dangers')
@login_required
@module_access_required('haccp', 'haccp.voir')
def dangers():
    return render_template('haccp/dangers.html')


@blueprint.route('/ccp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def ccp():
    return render_template('haccp/ccp.html')


@blueprint.route('/enregistrements')
@login_required
@module_access_required('haccp', 'haccp.voir')
def enregistrements():
    return render_template('haccp/enregistrements.html')


@blueprint.route('/prp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def prp():
    return render_template('haccp/prp.html')


@blueprint.route('/oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def oprp():
    return render_template('haccp/oprp.html')


@blueprint.route('/enregistrements-oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def enregistrements_oprp():
    return render_template('haccp/enregistrements_oprp.html')


@blueprint.route('/tracabilite')
@login_required
@module_access_required('haccp', 'haccp.voir')
def tracabilite():
    return render_template('haccp/tracabilite.html')


@blueprint.route('/rappels')
@login_required
@module_access_required('haccp', 'haccp.voir')
def rappels():
    return render_template('haccp/rappels.html')


# --- API: Analyse des dangers ---

@blueprint.route('/api/dangers')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_dangers():
    items = AnalyseDanger.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(AnalyseDanger.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'processus_id': r.processus_id,
        'type_danger': r.type_danger, 'danger': r.danger, 'cause': r.cause,
        'gravite': r.gravite, 'probabilite': r.probabilite,
        'detectabilite': r.detectabilite, 'ipr': r.ipr,
        'mesure_preventive': r.mesure_preventive,
        'est_significatif': r.est_significatif, 'justification': r.justification,
        'etape': r.processus.etape if r.processus else '',
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/dangers/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
def api_dangers_create():
    data = request.get_json()
    item = AnalyseDanger(
        entreprise_id=current_user.entreprise_id,
        processus_id=data.get('processus_id'),
        type_danger=data.get('type_danger', 'biologique'),
        danger=data.get('danger'), cause=data.get('cause'),
        gravite=data.get('gravite', 1),
        probabilite=data.get('probabilite', 1),
        detectabilite=data.get('detectabilite', 1),
        mesure_preventive=data.get('mesure_preventive'),
        est_significatif=data.get('est_significatif', False),
        justification=data.get('justification'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/dangers/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
def api_dangers_update(item_id):
    item = AnalyseDanger.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('processus_id', 'type_danger', 'danger', 'cause', 'gravite',
              'probabilite', 'detectabilite', 'mesure_preventive',
              'est_significatif', 'justification'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/dangers/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
def api_dangers_delete(item_id):
    item = AnalyseDanger.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Stats ---

@blueprint.route('/api/stats')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_stats():
    eid = current_user.entreprise_id
    return jsonify({
        'processus': ProcessusHaccp.query.filter_by(entreprise_id=eid).count(),
        'produits': ProduitHaccp.query.filter_by(entreprise_id=eid).count(),
        'ccp': Ccp.query.filter_by(entreprise_id=eid).count(),
        'dangers': AnalyseDanger.query.filter_by(entreprise_id=eid).count(),
        'nonconformites': NonConformite.query.filter_by(entreprise_id=eid, domaine='haccp').count(),
        'enregistrements': EnregistrementCcp.query.filter_by(entreprise_id=eid).count(),
        'prp': Prp.query.filter_by(entreprise_id=eid, type_prp='generic').count(),
        'oprp': Prp.query.filter_by(entreprise_id=eid, type_prp='operational').count(),
        'enregistrements_oprp': EnregistrementOprp.query.filter_by(entreprise_id=eid).count(),
        'tracabilite': TracabiliteLot.query.filter_by(entreprise_id=eid).count(),
        'rappels': RappelProduit.query.filter_by(entreprise_id=eid).count(),
    })


# --- API: Processus HACCP ---

@blueprint.route('/api/processus')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_processus():
    items = ProcessusHaccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ProcessusHaccp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'etape': r.etape, 'description': r.description,
        'danger': r.danger, 'type_danger': r.type_danger,
        'maitrise': r.maitrise, 'limite_critique': r.limite_critique,
        'surveillance': r.surveillance, 'frequence_surveillance': r.frequence_surveillance,
        'action_corrective': r.action_corrective, 'est_ccp': r.est_ccp,
        'num_ccp': r.num_ccp, 'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/processus/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
def api_processus_create():
    data = request.get_json()
    item = ProcessusHaccp(
        entreprise_id=current_user.entreprise_id,
        etape=data.get('etape'),
        description=data.get('description'),
        danger=data.get('danger'),
        type_danger=data.get('type_danger', 'biologique'),
        maitrise=data.get('maitrise'),
        limite_critique=data.get('limite_critique'),
        surveillance=data.get('surveillance'),
        frequence_surveillance=data.get('frequence_surveillance'),
        action_corrective=data.get('action_corrective'),
        est_ccp=data.get('est_ccp', False),
        num_ccp=data.get('num_ccp'),
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/processus/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
def api_processus_update(item_id):
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('etape', 'description', 'danger', 'type_danger', 'maitrise',
              'limite_critique', 'surveillance', 'frequence_surveillance',
              'action_corrective', 'num_ccp', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if 'est_ccp' in data:
        item.est_ccp = data['est_ccp']
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/processus/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
def api_processus_delete(item_id):
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Produits ---

@blueprint.route('/api/produits')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_produits():
    items = ProduitHaccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ProduitHaccp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'nom': r.nom, 'reference': r.reference,
        'description': r.description, 'duree_conservation': r.duree_conservation,
        'conditions_stockage': r.conditions_stockage,
        'utilisation_prevue': r.utilisation_prevue, 'type_client': r.type_client,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/produits/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
def api_produits_create():
    data = request.get_json()
    item = ProduitHaccp(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'), reference=data.get('reference'),
        description=data.get('description'),
        duree_conservation=data.get('duree_conservation'),
        conditions_stockage=data.get('conditions_stockage'),
        utilisation_prevue=data.get('utilisation_prevue'),
        type_client=data.get('type_client'), statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/produits/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
def api_produits_update(item_id):
    item = ProduitHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('nom', 'reference', 'description', 'duree_conservation',
              'conditions_stockage', 'utilisation_prevue', 'type_client', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/produits/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
def api_produits_delete(item_id):
    item = ProduitHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: CCP ---

@blueprint.route('/api/ccp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_ccp():
    items = Ccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Ccp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'code': r.code,
        'processus_id': r.processus_id, 'danger': r.danger,
        'limite_critique': r.limite_critique, 'tolerance': r.tolerance,
        'methode_surveillance': r.methode_surveillance,
        'frequence_surveillance': r.frequence_surveillance,
        'responsable': r.responsable, 'action_corrective': r.action_corrective,
        'procedure_derogation': r.procedure_derogation, 'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/ccp/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
def api_ccp_create():
    data = request.get_json()
    item = Ccp(
        entreprise_id=current_user.entreprise_id,
        processus_id=data.get('processus_id'),
        code=data.get('code'), danger=data.get('danger'),
        limite_critique=data.get('limite_critique'),
        tolerance=data.get('tolerance'),
        methode_surveillance=data.get('methode_surveillance'),
        frequence_surveillance=data.get('frequence_surveillance'),
        responsable=data.get('responsable'),
        action_corrective=data.get('action_corrective'),
        procedure_derogation=data.get('procedure_derogation'),
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/ccp/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
def api_ccp_update(item_id):
    item = Ccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('code', 'processus_id', 'danger', 'limite_critique', 'tolerance',
              'methode_surveillance', 'frequence_surveillance', 'responsable',
              'action_corrective', 'procedure_derogation', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/ccp/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
def api_ccp_delete(item_id):
    item = Ccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Enregistrements CCP ---

@blueprint.route('/api/enregistrements')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_enregistrements():
    items = EnregistrementCcp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EnregistrementCcp.date_controle.desc()).all()
    return jsonify([{
        'id': r.id, 'ccp_id': r.ccp_id,
        'date_controle': r.date_controle.isoformat() if r.date_controle else None,
        'valeur': r.valeur, 'unite': r.unite, 'conforme': r.conforme,
        'operateur': r.operateur, 'commentaire': r.commentaire,
        'action_entreprise': r.action_entreprise,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/enregistrements/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_create():
    data = request.get_json()
    date_val = datetime.fromisoformat(data['date_controle']) if data.get('date_controle') else datetime.utcnow()
    item = EnregistrementCcp(
        entreprise_id=current_user.entreprise_id,
        ccp_id=data.get('ccp_id'),
        date_controle=date_val,
        valeur=data.get('valeur'), unite=data.get('unite'),
        conforme=data.get('conforme', True),
        operateur=data.get('operateur'), commentaire=data.get('commentaire'),
        action_entreprise=data.get('action_entreprise'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/enregistrements/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_update(item_id):
    item = EnregistrementCcp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('ccp_id', 'valeur', 'unite', 'conforme', 'operateur',
              'commentaire', 'action_entreprise'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/enregistrements/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_delete(item_id):
    item = EnregistrementCcp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: PRP ---

@blueprint.route('/api/prp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_prp():
    items = Prp.query.filter_by(entreprise_id=current_user.entreprise_id, type_prp='generic')\
        .order_by(Prp.categorie, Prp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'categorie': r.categorie, 'element': r.element,
        'description': r.description, 'frequence': r.frequence,
        'responsable': r.responsable, 'procedure_reference': r.procedure_reference,
        'verifie_le': r.verifie_le.isoformat() if r.verifie_le else None,
        'prochaine_verification': r.prochaine_verification.isoformat() if r.prochaine_verification else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/prp/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_prp_create():
    data = request.get_json()
    item = Prp(
        entreprise_id=current_user.entreprise_id,
        categorie=data.get('categorie'), element=data.get('element'),
        description=data.get('description'), frequence=data.get('frequence'),
        responsable=data.get('responsable'),
        procedure_reference=data.get('procedure_reference'),
        verifie_le=datetime.strptime(data['verifie_le'], '%Y-%m-%d').date()
        if data.get('verifie_le') else None,
        prochaine_verification=datetime.strptime(data['prochaine_verification'], '%Y-%m-%d').date()
        if data.get('prochaine_verification') else None,
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/prp/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_prp_update(item_id):
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('categorie', 'element', 'description', 'frequence', 'responsable',
              'procedure_reference', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('verifie_le'):
        item.verifie_le = datetime.strptime(data['verifie_le'], '%Y-%m-%d').date()
    if data.get('prochaine_verification'):
        item.prochaine_verification = datetime.strptime(data['prochaine_verification'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/prp/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_prp_delete(item_id):
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: OPRP ---

@blueprint.route('/api/oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_oprp():
    items = Prp.query.filter_by(entreprise_id=current_user.entreprise_id, type_prp='operational')\
        .order_by(Prp.categorie, Prp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'categorie': r.categorie, 'element': r.element,
        'description': r.description, 'frequence': r.frequence,
        'responsable': r.responsable, 'procedure_reference': r.procedure_reference,
        'type_prp': r.type_prp,
        'processus_id': r.processus_id,
        'danger_id': r.danger_id,
        'limite_critique': r.limite_critique,
        'methode_surveillance': r.methode_surveillance,
        'frequence_surveillance': r.frequence_surveillance,
        'action_corrective': r.action_corrective,
        'etape': r.processus.etape if r.processus else '',
        'danger_libelle': r.danger.danger if r.danger else '',
        'verifie_le': r.verifie_le.isoformat() if r.verifie_le else None,
        'prochaine_verification': r.prochaine_verification.isoformat() if r.prochaine_verification else None,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/oprp/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_oprp_create():
    data = request.get_json()
    item = Prp(
        entreprise_id=current_user.entreprise_id,
        categorie=data.get('categorie', 'autre'),
        element=data.get('element'),
        description=data.get('description'),
        frequence=data.get('frequence'),
        responsable=data.get('responsable'),
        procedure_reference=data.get('procedure_reference'),
        type_prp='operational',
        processus_id=data.get('processus_id'),
        danger_id=data.get('danger_id'),
        limite_critique=data.get('limite_critique'),
        methode_surveillance=data.get('methode_surveillance'),
        frequence_surveillance=data.get('frequence_surveillance'),
        action_corrective=data.get('action_corrective'),
        verifie_le=datetime.strptime(data['verifie_le'], '%Y-%m-%d').date()
        if data.get('verifie_le') else None,
        prochaine_verification=datetime.strptime(data['prochaine_verification'], '%Y-%m-%d').date()
        if data.get('prochaine_verification') else None,
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/oprp/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_oprp_update(item_id):
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('categorie', 'element', 'description', 'frequence', 'responsable',
              'procedure_reference', 'processus_id', 'danger_id', 'limite_critique',
              'methode_surveillance', 'frequence_surveillance', 'action_corrective', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('verifie_le'):
        item.verifie_le = datetime.strptime(data['verifie_le'], '%Y-%m-%d').date()
    if data.get('prochaine_verification'):
        item.prochaine_verification = datetime.strptime(data['prochaine_verification'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/oprp/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_oprp_delete(item_id):
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Enregistrements OPRP ---

@blueprint.route('/api/enregistrements-oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_enregistrements_oprp():
    items = EnregistrementOprp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EnregistrementOprp.date_controle.desc()).all()
    return jsonify([{
        'id': r.id, 'oprp_id': r.oprp_id,
        'date_controle': r.date_controle.isoformat() if r.date_controle else None,
        'valeur': r.valeur, 'unite': r.unite, 'conforme': r.conforme,
        'operateur': r.operateur, 'commentaire': r.commentaire,
        'action_entreprise': r.action_entreprise,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/enregistrements-oprp/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_oprp_create():
    data = request.get_json()
    date_val = datetime.fromisoformat(data['date_controle']) if data.get('date_controle') else datetime.utcnow()
    item = EnregistrementOprp(
        entreprise_id=current_user.entreprise_id,
        oprp_id=data.get('oprp_id'),
        date_controle=date_val,
        valeur=data.get('valeur'), unite=data.get('unite'),
        conforme=data.get('conforme', True),
        operateur=data.get('operateur'), commentaire=data.get('commentaire'),
        action_entreprise=data.get('action_entreprise'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/enregistrements-oprp/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_oprp_update(item_id):
    item = EnregistrementOprp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('oprp_id', 'valeur', 'unite', 'conforme', 'operateur',
              'commentaire', 'action_entreprise'):
        if f in data:
            setattr(item, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/enregistrements-oprp/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_oprp_delete(item_id):
    item = EnregistrementOprp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Traçabilité ---

@blueprint.route('/api/tracabilite')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_tracabilite():
    items = TracabiliteLot.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(TracabiliteLot.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'code_lot': r.code_lot, 'produit_nom': r.produit_nom,
        'date_fabrication': r.date_fabrication.isoformat() if r.date_fabrication else None,
        'date_expiration': r.date_expiration.isoformat() if r.date_expiration else None,
        'quantite': r.quantite, 'fournisseur': r.fournisseur,
        'lot_fournisseur': r.lot_fournisseur,
        'matieres_utilisees': r.matieres_utilisees,
        'statut': r.statut, 'notes': r.notes,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/tracabilite/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
def api_tracabilite_create():
    data = request.get_json()
    item = TracabiliteLot(
        entreprise_id=current_user.entreprise_id,
        code_lot=data.get('code_lot'), produit_nom=data.get('produit_nom'),
        date_fabrication=datetime.strptime(data['date_fabrication'], '%Y-%m-%d').date()
        if data.get('date_fabrication') else None,
        date_expiration=datetime.strptime(data['date_expiration'], '%Y-%m-%d').date()
        if data.get('date_expiration') else None,
        quantite=data.get('quantite'), fournisseur=data.get('fournisseur'),
        lot_fournisseur=data.get('lot_fournisseur'),
        matieres_utilisees=data.get('matieres_utilisees'),
        statut=data.get('statut', 'disponible'), notes=data.get('notes'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/tracabilite/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
def api_tracabilite_update(item_id):
    item = TracabiliteLot.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('code_lot', 'produit_nom', 'quantite', 'fournisseur',
              'lot_fournisseur', 'matieres_utilisees', 'statut', 'notes'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_fabrication'):
        item.date_fabrication = datetime.strptime(data['date_fabrication'], '%Y-%m-%d').date()
    if data.get('date_expiration'):
        item.date_expiration = datetime.strptime(data['date_expiration'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/tracabilite/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
def api_tracabilite_delete(item_id):
    item = TracabiliteLot.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Rappels ---

@blueprint.route('/api/rappels')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_rappels():
    items = RappelProduit.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(RappelProduit.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'reference': r.reference, 'produit': r.produit,
        'lot': r.lot,
        'date_rappel': r.date_rappel.isoformat() if r.date_rappel else None,
        'motif': r.motif, 'gravite': r.gravite,
        'actions_menées': r.actions_menées,
        'client_notifie': r.client_notifie,
        'autorite_notifiee': r.autorite_notifiee,
        'statut': r.statut,
        'cloture_le': r.cloture_le.isoformat() if r.cloture_le else None,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/rappels/create', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
def api_rappels_create():
    data = request.get_json()
    item = RappelProduit(
        entreprise_id=current_user.entreprise_id,
        reference=data.get('reference'), produit=data.get('produit'),
        lot=data.get('lot'),
        date_rappel=datetime.strptime(data['date_rappel'], '%Y-%m-%d').date()
        if data.get('date_rappel') else date.today(),
        motif=data.get('motif'), gravite=data.get('gravite'),
        actions_menées=data.get('actions_menées'),
        client_notifie=data.get('client_notifie', False),
        autorite_notifiee=data.get('autorite_notifiee', False),
        statut=data.get('statut', 'en_cours'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/rappels/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
def api_rappels_update(item_id):
    item = RappelProduit.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    for f in ('reference', 'produit', 'lot', 'motif', 'gravite',
              'actions_menées', 'client_notifie', 'autorite_notifiee', 'statut'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_rappel'):
        item.date_rappel = datetime.strptime(data['date_rappel'], '%Y-%m-%d').date()
    if data.get('cloture_le'):
        item.cloture_le = datetime.strptime(data['cloture_le'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/rappels/<int:item_id>/delete', methods=['POST'])
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
def api_rappels_delete(item_id):
    item = RappelProduit.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
