from flask import render_template, request, jsonify, abort, Response
from flask_login import login_required, current_user
from app import db
from app.models import (Risque, ProcessusHaccp, ReclamationClient, Fournisseur,
    Formation, Equipement, ControleQualite, RevueDirection, NonConformiteQualite,
    Entreprise)
from app.qualite import blueprint
from datetime import date, datetime
import csv
import io


def _check_qualite_access():
    entreprise = db.session.get(Entreprise, current_user.entreprise_id)
    if not entreprise or 'qualite' not in (entreprise.modules_actifs or []):
        abort(403)
    if not current_user.has_permission('qualite.voir', current_user.entreprise_id):
        abort(403)


# --- Page routes ---

@blueprint.route('/')
@login_required
def tableau_de_bord():
    _check_qualite_access()
    return render_template('qualite/tableau_de_bord.html')

@blueprint.route('/risques')
@login_required
def risques():
    _check_qualite_access()
    return render_template('qualite/risques.html')

@blueprint.route('/haccp')
@login_required
def haccp():
    _check_qualite_access()
    return render_template('qualite/haccp.html')

@blueprint.route('/clients')
@login_required
def clients():
    _check_qualite_access()
    return render_template('qualite/clients.html')

@blueprint.route('/fournisseurs')
@login_required
def fournisseurs():
    _check_qualite_access()
    return render_template('qualite/fournisseurs.html')

@blueprint.route('/formations')
@login_required
def formations():
    _check_qualite_access()
    return render_template('qualite/formations.html')

@blueprint.route('/equipements')
@login_required
def equipements():
    _check_qualite_access()
    return render_template('qualite/equipements.html')

@blueprint.route('/controle')
@login_required
def controle():
    _check_qualite_access()
    return render_template('qualite/controle.html')

@blueprint.route('/revue')
@login_required
def revue():
    _check_qualite_access()
    return render_template('qualite/revue.html')

@blueprint.route('/nonconformites')
@login_required
def nonconformites():
    _check_qualite_access()
    return render_template('qualite/nonconformites.html')


# --- API: Stats ---

@blueprint.route('/api/stats')
@login_required
def api_stats():
    _check_qualite_access()
    eid = current_user.entreprise_id
    return jsonify({
        'risques': Risque.query.filter_by(entreprise_id=eid).count(),
        'haccp': ProcessusHaccp.query.filter_by(entreprise_id=eid).count(),
        'reclamations': ReclamationClient.query.filter_by(entreprise_id=eid).count(),
        'fournisseurs': Fournisseur.query.filter_by(entreprise_id=eid).count(),
        'formations': Formation.query.filter_by(entreprise_id=eid).count(),
        'equipements': Equipement.query.filter_by(entreprise_id=eid).count(),
        'controles': ControleQualite.query.filter_by(entreprise_id=eid).count(),
        'revues': RevueDirection.query.filter_by(entreprise_id=eid).count(),
        'nonconformites': NonConformiteQualite.query.filter_by(entreprise_id=eid).count(),
    })


# --- API: Risques ---

@blueprint.route('/api/risques')
@login_required
def api_risques():
    _check_qualite_access()
    items = Risque.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Risque.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'designation': r.designation,
        'cause': r.cause,
        'effet': r.effet,
        'gravite': r.gravite,
        'probabilite': r.probabilite,
        'detection': r.detection,
        'ipr': r.ipr,
        'maitrise': r.maitrise,
        'statut': r.statut,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'responsable_id': r.responsable_id,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/risques/create', methods=['POST'])
@login_required
def api_risques_create():
    _check_qualite_access()
    data = request.get_json()
    item = Risque(
        entreprise_id=current_user.entreprise_id,
        designation=data.get('designation'),
        cause=data.get('cause'),
        effet=data.get('effet'),
        gravite=int(data.get('gravite', 1)),
        probabilite=int(data.get('probabilite', 1)),
        detection=int(data.get('detection', 1)),
        maitrise=data.get('maitrise'),
        statut=data.get('statut', 'identifie'),
        responsable_id=data.get('responsable_id', type=int),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/risques/<int:item_id>/update', methods=['POST'])
@login_required
def api_risques_update(item_id):
    _check_qualite_access()
    item = Risque.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    item.designation = data.get('designation', item.designation)
    item.cause = data.get('cause', item.cause)
    item.effet = data.get('effet', item.effet)
    item.gravite = int(data.get('gravite', item.gravite))
    item.probabilite = int(data.get('probabilite', item.probabilite))
    item.detection = int(data.get('detection', item.detection))
    item.maitrise = data.get('maitrise', item.maitrise)
    item.statut = data.get('statut', item.statut)
    item.responsable_id = data.get('responsable_id', item.responsable_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/risques/<int:item_id>/delete', methods=['POST'])
@login_required
def api_risques_delete(item_id):
    _check_qualite_access()
    item = Risque.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: HACCP ---

@blueprint.route('/api/haccp')
@login_required
def api_haccp():
    _check_qualite_access()
    items = ProcessusHaccp.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ProcessusHaccp.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'etape': r.etape,
        'danger': r.danger,
        'maitrise': r.maitrise,
        'limite_critique': r.limite_critique,
        'surveillance': r.surveillance,
        'action_corrective': r.action_corrective,
        'est_ccp': r.est_ccp,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/haccp/create', methods=['POST'])
@login_required
def api_haccp_create():
    _check_qualite_access()
    data = request.get_json()
    item = ProcessusHaccp(
        entreprise_id=current_user.entreprise_id,
        etape=data.get('etape'),
        danger=data.get('danger'),
        maitrise=data.get('maitrise'),
        limite_critique=data.get('limite_critique'),
        surveillance=data.get('surveillance'),
        action_corrective=data.get('action_corrective'),
        est_ccp=data.get('est_ccp', type=bool),
        statut=data.get('statut', 'actif'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/haccp/<int:item_id>/update', methods=['POST'])
@login_required
def api_haccp_update(item_id):
    _check_qualite_access()
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    item.etape = data.get('etape', item.etape)
    item.danger = data.get('danger', item.danger)
    item.maitrise = data.get('maitrise', item.maitrise)
    item.limite_critique = data.get('limite_critique', item.limite_critique)
    item.surveillance = data.get('surveillance', item.surveillance)
    item.action_corrective = data.get('action_corrective', item.action_corrective)
    item.est_ccp = data.get('est_ccp', item.est_ccp)
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/haccp/<int:item_id>/delete', methods=['POST'])
@login_required
def api_haccp_delete(item_id):
    _check_qualite_access()
    item = ProcessusHaccp.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Réclamations clients ---

@blueprint.route('/api/clients')
@login_required
def api_clients():
    _check_qualite_access()
    items = ReclamationClient.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ReclamationClient.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_reclamation': r.date_reclamation.isoformat() if r.date_reclamation else None,
        'client': r.client,
        'produit': r.produit,
        'description': r.description,
        'action': r.action,
        'statut': r.statut,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'responsable_id': r.responsable_id,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/clients/create', methods=['POST'])
@login_required
def api_clients_create():
    _check_qualite_access()
    data = request.get_json()
    date_val = datetime.strptime(data['date_reclamation'], '%Y-%m-%d').date() if data.get('date_reclamation') else date.today()
    item = ReclamationClient(
        entreprise_id=current_user.entreprise_id,
        date_reclamation=date_val,
        client=data.get('client'),
        produit=data.get('produit'),
        description=data.get('description'),
        action=data.get('action'),
        statut=data.get('statut', 'ouverte'),
        responsable_id=data.get('responsable_id', type=int),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/clients/<int:item_id>/update', methods=['POST'])
@login_required
def api_clients_update(item_id):
    _check_qualite_access()
    item = ReclamationClient.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('date_reclamation'):
        item.date_reclamation = datetime.strptime(data['date_reclamation'], '%Y-%m-%d').date()
    item.client = data.get('client', item.client)
    item.produit = data.get('produit', item.produit)
    item.description = data.get('description', item.description)
    item.action = data.get('action', item.action)
    item.statut = data.get('statut', item.statut)
    item.responsable_id = data.get('responsable_id', item.responsable_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/clients/<int:item_id>/delete', methods=['POST'])
@login_required
def api_clients_delete(item_id):
    _check_qualite_access()
    item = ReclamationClient.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Fournisseurs ---

@blueprint.route('/api/fournisseurs')
@login_required
def api_fournisseurs():
    _check_qualite_access()
    items = Fournisseur.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Fournisseur.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'nom': r.nom,
        'produit': r.produit,
        'evaluation': r.evaluation,
        'statut': r.statut,
        'dernier_audit': r.dernier_audit.isoformat() if r.dernier_audit else None,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/fournisseurs/create', methods=['POST'])
@login_required
def api_fournisseurs_create():
    _check_qualite_access()
    data = request.get_json()
    item = Fournisseur(
        entreprise_id=current_user.entreprise_id,
        nom=data.get('nom'),
        produit=data.get('produit'),
        evaluation=data.get('evaluation', type=int),
        statut=data.get('statut', 'actif'),
        dernier_audit=datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
        if data.get('dernier_audit') else None,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/fournisseurs/<int:item_id>/update', methods=['POST'])
@login_required
def api_fournisseurs_update(item_id):
    _check_qualite_access()
    item = Fournisseur.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    item.nom = data.get('nom', item.nom)
    item.produit = data.get('produit', item.produit)
    item.evaluation = data.get('evaluation', item.evaluation)
    item.statut = data.get('statut', item.statut)
    if data.get('dernier_audit'):
        item.dernier_audit = datetime.strptime(data['dernier_audit'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/fournisseurs/<int:item_id>/delete', methods=['POST'])
@login_required
def api_fournisseurs_delete(item_id):
    _check_qualite_access()
    item = Fournisseur.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Formations ---

@blueprint.route('/api/formations')
@login_required
def api_formations():
    _check_qualite_access()
    items = Formation.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Formation.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'titre': r.titre,
        'formateur': r.formateur,
        'participants': r.participants,
        'date_formation': r.date_formation.isoformat() if r.date_formation else None,
        'duree_heures': r.duree_heures,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/formations/create', methods=['POST'])
@login_required
def api_formations_create():
    _check_qualite_access()
    data = request.get_json()
    item = Formation(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'),
        formateur=data.get('formateur'),
        participants=data.get('participants'),
        date_formation=datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
        if data.get('date_formation') else None,
        duree_heures=data.get('duree_heures', type=float),
        statut=data.get('statut', 'planifiee'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/formations/<int:item_id>/update', methods=['POST'])
@login_required
def api_formations_update(item_id):
    _check_qualite_access()
    item = Formation.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    item.titre = data.get('titre', item.titre)
    item.formateur = data.get('formateur', item.formateur)
    item.participants = data.get('participants', item.participants)
    if data.get('date_formation'):
        item.date_formation = datetime.strptime(data['date_formation'], '%Y-%m-%d').date()
    item.duree_heures = data.get('duree_heures', item.duree_heures)
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/formations/<int:item_id>/delete', methods=['POST'])
@login_required
def api_formations_delete(item_id):
    _check_qualite_access()
    item = Formation.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Équipements ---

@blueprint.route('/api/equipements')
@login_required
def api_equipements():
    _check_qualite_access()
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
def api_equipements_create():
    _check_qualite_access()
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
def api_equipements_update(item_id):
    _check_qualite_access()
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
def api_equipements_delete(item_id):
    _check_qualite_access()
    item = Equipement.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Contrôle qualité ---

@blueprint.route('/api/controle')
@login_required
def api_controle():
    _check_qualite_access()
    items = ControleQualite.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(ControleQualite.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_controle': r.date_controle.isoformat() if r.date_controle else None,
        'produit': r.produit,
        'lot': r.lot,
        'type_controle': r.type_controle,
        'resultat': r.resultat,
        'valeur': r.valeur,
        'specification': r.specification,
        'inspecteur': r.inspecteur,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/controle/create', methods=['POST'])
@login_required
def api_controle_create():
    _check_qualite_access()
    data = request.get_json()
    date_val = datetime.strptime(data['date_controle'], '%Y-%m-%d').date() if data.get('date_controle') else date.today()
    item = ControleQualite(
        entreprise_id=current_user.entreprise_id,
        date_controle=date_val,
        produit=data.get('produit'),
        lot=data.get('lot'),
        type_controle=data.get('type_controle'),
        resultat=data.get('resultat'),
        valeur=data.get('valeur'),
        specification=data.get('specification'),
        inspecteur=data.get('inspecteur'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/controle/<int:item_id>/update', methods=['POST'])
@login_required
def api_controle_update(item_id):
    _check_qualite_access()
    item = ControleQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('date_controle'):
        item.date_controle = datetime.strptime(data['date_controle'], '%Y-%m-%d').date()
    item.produit = data.get('produit', item.produit)
    item.lot = data.get('lot', item.lot)
    item.type_controle = data.get('type_controle', item.type_controle)
    item.resultat = data.get('resultat', item.resultat)
    item.valeur = data.get('valeur', item.valeur)
    item.specification = data.get('specification', item.specification)
    item.inspecteur = data.get('inspecteur', item.inspecteur)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/controle/<int:item_id>/delete', methods=['POST'])
@login_required
def api_controle_delete(item_id):
    _check_qualite_access()
    item = ControleQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Revue de direction ---

@blueprint.route('/api/revue')
@login_required
def api_revue():
    _check_qualite_access()
    items = RevueDirection.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(RevueDirection.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_revue': r.date_revue.isoformat() if r.date_revue else None,
        'participants': r.participants,
        'decisions': r.decisions,
        'suivi': r.suivi,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/revue/create', methods=['POST'])
@login_required
def api_revue_create():
    _check_qualite_access()
    data = request.get_json()
    date_val = datetime.strptime(data['date_revue'], '%Y-%m-%d').date() if data.get('date_revue') else date.today()
    item = RevueDirection(
        entreprise_id=current_user.entreprise_id,
        date_revue=date_val,
        participants=data.get('participants'),
        decisions=data.get('decisions'),
        suivi=data.get('suivi'),
        statut=data.get('statut', 'realisee'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/revue/<int:item_id>/update', methods=['POST'])
@login_required
def api_revue_update(item_id):
    _check_qualite_access()
    item = RevueDirection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('date_revue'):
        item.date_revue = datetime.strptime(data['date_revue'], '%Y-%m-%d').date()
    item.participants = data.get('participants', item.participants)
    item.decisions = data.get('decisions', item.decisions)
    item.suivi = data.get('suivi', item.suivi)
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/revue/<int:item_id>/delete', methods=['POST'])
@login_required
def api_revue_delete(item_id):
    _check_qualite_access()
    item = RevueDirection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Non-conformités qualité ---

@blueprint.route('/api/nonconformites')
@login_required
def api_nonconformites():
    _check_qualite_access()
    items = NonConformiteQualite.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(NonConformiteQualite.date_creation.desc()).all()
    return jsonify([{
        'id': r.id,
        'date_nc': r.date_nc.isoformat() if r.date_nc else None,
        'reference': r.reference,
        'produit_processus': r.produit_processus,
        'description': r.description,
        'action_corrective': r.action_corrective,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'responsable_id': r.responsable_id,
        'statut': r.statut,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/nonconformites/create', methods=['POST'])
@login_required
def api_nonconformites_create():
    _check_qualite_access()
    data = request.get_json()
    date_val = datetime.strptime(data['date_nc'], '%Y-%m-%d').date() if data.get('date_nc') else date.today()
    item = NonConformiteQualite(
        entreprise_id=current_user.entreprise_id,
        date_nc=date_val,
        reference=data.get('reference'),
        produit_processus=data.get('produit_processus'),
        description=data.get('description'),
        action_corrective=data.get('action_corrective'),
        responsable_id=data.get('responsable_id', type=int),
        statut=data.get('statut', 'ouverte'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/nonconformites/<int:item_id>/update', methods=['POST'])
@login_required
def api_nonconformites_update(item_id):
    _check_qualite_access()
    item = NonConformiteQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    data = request.get_json()
    if data.get('date_nc'):
        item.date_nc = datetime.strptime(data['date_nc'], '%Y-%m-%d').date()
    item.reference = data.get('reference', item.reference)
    item.produit_processus = data.get('produit_processus', item.produit_processus)
    item.description = data.get('description', item.description)
    item.action_corrective = data.get('action_corrective', item.action_corrective)
    item.responsable_id = data.get('responsable_id', item.responsable_id)
    item.statut = data.get('statut', item.statut)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/nonconformites/<int:item_id>/delete', methods=['POST'])
@login_required
def api_nonconformites_delete(item_id):
    _check_qualite_access()
    item = NonConformiteQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/risques/export')
@login_required
def export_risques():
    _check_qualite_access()
    risques = Risque.query.filter_by(entreprise_id=current_user.entreprise_id)\
        .order_by(Risque.date_creation.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Désignation', 'Cause', 'Effet', 'Gravité', 'Probabilité', 'Détection', 'IPR', 'Maîtrise', 'Statut', 'Créé le'])
    for r in risques:
        writer.writerow([
            r.id,
            r.designation or '',
            r.cause or '',
            r.effet or '',
            r.gravite,
            r.probabilite,
            r.detection,
            r.ipr,
            r.maitrise or '',
            r.statut or '',
            r.date_creation.strftime('%d/%m/%Y') if r.date_creation else '',
        ])

    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=risques_export.csv'}
    )
