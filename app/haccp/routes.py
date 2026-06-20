from flask import render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.haccp import blueprint
from app.models import (
    ProcessusHaccp, ProduitHaccp, AnalyseDanger, Ccp,
    EnregistrementCcp, Prp, EnregistrementOprp,
    TracabiliteLot, RappelProduit,
)
from app.models.nonconformite import NonConformite
from app.schemas.haccp import (
    ProcessusHaccpSchema, ProduitHaccpSchema, AnalyseDangerSchema,
    CcpSchema, EnregistrementCcpSchema, PrpSchema, EnregistrementOprpSchema,
    TracabiliteLotSchema, RappelProduitSchema
)
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

# --- API: Analyse des dangers ---

@blueprint.get('/api/dangers')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, AnalyseDangerSchema(many=True))
def api_dangers():
    """Liste des analyses de dangers"""
    return AnalyseDanger.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(AnalyseDanger.date_creation.desc()).all()


@blueprint.post('/api/dangers/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
@blueprint.arguments(AnalyseDangerSchema)
@blueprint.response(201, AnalyseDangerSchema)
def api_dangers_create(data):
    """Créer une analyse de danger"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/dangers/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
@blueprint.arguments(AnalyseDangerSchema(partial=True))
@blueprint.response(200, AnalyseDangerSchema)
def api_dangers_update(data, item_id):
    """Mettre à jour une analyse de danger"""
    item = AnalyseDanger.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/dangers/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_dangers')
def api_dangers_delete(item_id):
    """Supprimer une analyse de danger"""
    item = AnalyseDanger.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Stats ---

@blueprint.get('/api/stats')
@login_required
@module_access_required('haccp', 'haccp.voir')
def api_stats():
    """Statistiques HACCP"""
    eid = current_user.entreprise_id
    return {
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
    }


# --- API: Processus HACCP ---

@blueprint.get('/api/processus')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, ProcessusHaccpSchema(many=True))
def api_processus():
    """Liste des étapes du processus HACCP"""
    return ProcessusHaccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ProcessusHaccp.date_creation.desc()).all()


@blueprint.post('/api/processus/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
@blueprint.arguments(ProcessusHaccpSchema)
@blueprint.response(201, ProcessusHaccpSchema)
def api_processus_create(data):
    """Créer une étape de processus"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/processus/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
@blueprint.arguments(ProcessusHaccpSchema(partial=True))
@blueprint.response(200, ProcessusHaccpSchema)
def api_processus_update(data, item_id):
    """Mettre à jour une étape de processus"""
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/processus/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_processus')
def api_processus_delete(item_id):
    """Supprimer une étape de processus"""
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Produits ---

@blueprint.get('/api/produits')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, ProduitHaccpSchema(many=True))
def api_produits():
    """Liste des produits HACCP"""
    return ProduitHaccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ProduitHaccp.date_creation.desc()).all()


@blueprint.post('/api/produits/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
@blueprint.arguments(ProduitHaccpSchema)
@blueprint.response(201, ProduitHaccpSchema)
def api_produits_create(data):
    """Créer un produit"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/produits/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
@blueprint.arguments(ProduitHaccpSchema(partial=True))
@blueprint.response(200, ProduitHaccpSchema)
def api_produits_update(data, item_id):
    """Mettre à jour un produit"""
    item = ProduitHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/produits/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_produits')
def api_produits_delete(item_id):
    """Supprimer un produit"""
    item = ProduitHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: CCP ---

@blueprint.get('/api/ccp')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, CcpSchema(many=True))
def api_ccp():
    """Liste des CCP (Points de Contrôle Critique)"""
    return Ccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Ccp.date_creation.desc()).all()


@blueprint.post('/api/ccp/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
@blueprint.arguments(CcpSchema)
@blueprint.response(201, CcpSchema)
def api_ccp_create(data):
    """Créer un CCP"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/ccp/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
@blueprint.arguments(CcpSchema(partial=True))
@blueprint.response(200, CcpSchema)
def api_ccp_update(data, item_id):
    """Mettre à jour un CCP"""
    item = Ccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/ccp/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_ccp')
def api_ccp_delete(item_id):
    """Supprimer un CCP"""
    item = Ccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Enregistrements CCP ---

@blueprint.get('/api/enregistrements')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, EnregistrementCcpSchema(many=True))
def api_enregistrements():
    """Liste des enregistrements de contrôle CCP"""
    return EnregistrementCcp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EnregistrementCcp.date_controle.desc()).all()


@blueprint.post('/api/enregistrements/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementCcpSchema)
@blueprint.response(201, EnregistrementCcpSchema)
def api_enregistrements_create(data):
    """Créer un enregistrement de contrôle CCP"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/enregistrements/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementCcpSchema(partial=True))
@blueprint.response(200, EnregistrementCcpSchema)
def api_enregistrements_update(data, item_id):
    """Mettre à jour un enregistrement de contrôle CCP"""
    item = EnregistrementCcp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/enregistrements/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_delete(item_id):
    """Supprimer un enregistrement de contrôle CCP"""
    item = EnregistrementCcp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: PRP ---

@blueprint.get('/api/prp')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, PrpSchema(many=True))
def api_prp():
    """Liste des PRP (Programmes Prérequis)"""
    return Prp.query.filter_by(entreprise_id=current_user.entreprise_id, type_prp='generic')\
        .order_by(Prp.categorie, Prp.date_creation.desc()).all()


@blueprint.post('/api/prp/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
@blueprint.arguments(PrpSchema)
@blueprint.response(201, PrpSchema)
def api_prp_create(data):
    """Créer un PRP"""
    data.entreprise_id = current_user.entreprise_id
    data.type_prp = 'generic'
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/prp/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
@blueprint.arguments(PrpSchema(partial=True))
@blueprint.response(200, PrpSchema)
def api_prp_update(data, item_id):
    """Mettre à jour un PRP"""
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/prp/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_prp_delete(item_id):
    """Supprimer un PRP"""
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: OPRP ---

@blueprint.get('/api/oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, PrpSchema(many=True))
def api_oprp():
    """Liste des OPRP (Programmes Prérequis Opérationnels)"""
    return Prp.query.filter_by(entreprise_id=current_user.entreprise_id, type_prp='operational')\
        .order_by(Prp.categorie, Prp.date_creation.desc()).all()


@blueprint.post('/api/oprp/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
@blueprint.arguments(PrpSchema)
@blueprint.response(201, PrpSchema)
def api_oprp_create(data):
    """Créer un OPRP"""
    data.entreprise_id = current_user.entreprise_id
    data.type_prp = 'operational'
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/oprp/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
@blueprint.arguments(PrpSchema(partial=True))
@blueprint.response(200, PrpSchema)
def api_oprp_update(data, item_id):
    """Mettre à jour un OPRP"""
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/oprp/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_prp')
def api_oprp_delete(item_id):
    """Supprimer un OPRP"""
    item = Prp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Enregistrements OPRP ---

@blueprint.get('/api/enregistrements-oprp')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, EnregistrementOprpSchema(many=True))
def api_enregistrements_oprp():
    """Liste des enregistrements de contrôle OPRP"""
    return EnregistrementOprp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(EnregistrementOprp.date_controle.desc()).all()


@blueprint.post('/api/enregistrements-oprp/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementOprpSchema)
@blueprint.response(201, EnregistrementOprpSchema)
def api_enregistrements_oprp_create(data):
    """Créer un enregistrement de contrôle OPRP"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/enregistrements-oprp/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
@blueprint.arguments(EnregistrementOprpSchema(partial=True))
@blueprint.response(200, EnregistrementOprpSchema)
def api_enregistrements_oprp_update(data, item_id):
    """Mettre à jour un enregistrement de contrôle OPRP"""
    item = EnregistrementOprp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/enregistrements-oprp/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_enregistrements')
def api_enregistrements_oprp_delete(item_id):
    """Supprimer un enregistrement de contrôle OPRP"""
    item = EnregistrementOprp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Traçabilité ---

@blueprint.get('/api/tracabilite')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, TracabiliteLotSchema(many=True))
def api_tracabilite():
    """Liste des lots pour la traçabilité"""
    return TracabiliteLot.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(TracabiliteLot.date_creation.desc()).all()


@blueprint.post('/api/tracabilite/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
@blueprint.arguments(TracabiliteLotSchema)
@blueprint.response(201, TracabiliteLotSchema)
def api_tracabilite_create(data):
    """Créer un lot de traçabilité"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/tracabilite/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
@blueprint.arguments(TracabiliteLotSchema(partial=True))
@blueprint.response(200, TracabiliteLotSchema)
def api_tracabilite_update(data, item_id):
    """Mettre à jour un lot de traçabilité"""
    item = TracabiliteLot.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/tracabilite/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_tracabilite')
def api_tracabilite_delete(item_id):
    """Supprimer un lot de traçabilité"""
    item = TracabiliteLot.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


# --- API: Rappels ---

@blueprint.get('/api/rappels')
@login_required
@module_access_required('haccp', 'haccp.voir')
@blueprint.response(200, RappelProduitSchema(many=True))
def api_rappels():
    """Liste des rappels produits"""
    return RappelProduit.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(RappelProduit.date_creation.desc()).all()


@blueprint.post('/api/rappels/create')
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
@blueprint.arguments(RappelProduitSchema)
@blueprint.response(201, RappelProduitSchema)
def api_rappels_create(data):
    """Créer un rappel produit"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/rappels/<int:item_id>/update')
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
@blueprint.arguments(RappelProduitSchema(partial=True))
@blueprint.response(200, RappelProduitSchema)
def api_rappels_update(data, item_id):
    """Mettre à jour un rappel produit"""
    item = RappelProduit.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/rappels/<int:item_id>/delete')
@login_required
@module_access_required('haccp', 'haccp.gerer_rappels')
def api_rappels_delete(item_id):
    """Supprimer un rappel produit"""
    item = RappelProduit.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}
