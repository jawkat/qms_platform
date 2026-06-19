from flask import render_template, request, jsonify, abort, Response, redirect, url_for
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import (Risque, ReclamationClient, Fournisseur,
    Formation, Equipement, ControleQualite, RevueDirection,
    Entreprise)
from app.models.nonconformite import NonConformite
from app.qualite import blueprint
from datetime import date, datetime
import csv
import io




# --- Page routes ---

@blueprint.route('/')
@login_required
@module_access_required('qualite', 'qualite.voir')
def tableau_de_bord():
    return render_template('qualite/tableau_de_bord.html')

@blueprint.route('/risques')
@login_required
@module_access_required('qualite', 'qualite.voir')
def risques():
    return render_template('qualite/risques.html')


@blueprint.route('/clients')
@login_required
@module_access_required('qualite', 'qualite.voir')
def clients():
    return redirect(url_for('reclamations.index'))

@blueprint.route('/fournisseurs')
@login_required
@module_access_required('qualite', 'qualite.voir')
def fournisseurs():
    return redirect(url_for('fournisseurs.index'))

@blueprint.route('/formations')
@login_required
@module_access_required('qualite', 'qualite.voir')
def formations():
    return redirect(url_for('formations.index'))

@blueprint.route('/equipements')
@login_required
@module_access_required('qualite', 'qualite.voir')
def equipements():
    return render_template('qualite/equipements.html')

@blueprint.route('/controle')
@login_required
@module_access_required('qualite', 'qualite.voir')
def controle():
    return render_template('qualite/controle.html')

@blueprint.route('/revue')
@login_required
@module_access_required('qualite', 'qualite.voir')
def revue():
    return render_template('qualite/revue.html')

# --- API: Stats ---

@blueprint.route('/api/stats')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_stats():
    eid = current_user.entreprise_id
    return jsonify({
        'risques': Risque.query.filter_by(entreprise_id=eid).count(),

        'reclamations': ReclamationClient.query.filter_by(entreprise_id=eid).count(),
        'fournisseurs': Fournisseur.query.filter_by(entreprise_id=eid).count(),
        'formations': Formation.query.filter_by(entreprise_id=eid).count(),
        'equipements': Equipement.query.filter_by(entreprise_id=eid).count(),
        'controles': ControleQualite.query.filter_by(entreprise_id=eid).count(),
        'revues': RevueDirection.query.filter_by(entreprise_id=eid).count(),
        'nonconformites': NonConformite.query.filter_by(entreprise_id=eid, domaine='qualite').count(),
    })


# --- API: Risques ---

@blueprint.route('/api/risques')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques():
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
@module_access_required('qualite', 'qualite.voir')
def api_risques_create():
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
        responsable_id=data.get('responsable_id'),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id})


@blueprint.route('/api/risques/<int:item_id>/update', methods=['POST'])
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_update(item_id):
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
@module_access_required('qualite', 'qualite.voir')
def api_risques_delete(item_id):
    item = Risque.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Équipements ---

@blueprint.route('/api/equipements')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_equipements():
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
@module_access_required('qualite', 'qualite.voir')
def api_equipements_create():
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
@module_access_required('qualite', 'qualite.voir')
def api_equipements_update(item_id):
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
@module_access_required('qualite', 'qualite.voir')
def api_equipements_delete(item_id):
    item = Equipement.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Contrôle qualité ---

@blueprint.route('/api/controle')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_controle():
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
@module_access_required('qualite', 'qualite.voir')
def api_controle_create():
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
@module_access_required('qualite', 'qualite.voir')
def api_controle_update(item_id):
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
@module_access_required('qualite', 'qualite.voir')
def api_controle_delete(item_id):
    item = ControleQualite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})


# --- API: Revue de direction ---

@blueprint.route('/api/revue')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_revue():
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
@module_access_required('qualite', 'qualite.voir')
def api_revue_create():
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
@module_access_required('qualite', 'qualite.voir')
def api_revue_update(item_id):
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
@module_access_required('qualite', 'qualite.voir')
def api_revue_delete(item_id):
    item = RevueDirection.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})



@blueprint.route('/api/risques/export')
@login_required
@module_access_required('qualite', 'qualite.voir')
def export_risques():
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
