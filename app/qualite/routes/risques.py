from flask import render_template, request, jsonify, Response
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import Risque
from app.qualite import blueprint
from datetime import date, datetime
import csv
import io


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
    from flask import redirect, url_for
    return redirect(url_for('reclamations.index'))


@blueprint.route('/fournisseurs')
@login_required
@module_access_required('qualite', 'qualite.voir')
def fournisseurs():
    from flask import redirect, url_for
    return redirect(url_for('fournisseurs.index'))


@blueprint.route('/formations')
@login_required
@module_access_required('qualite', 'qualite.voir')
def formations():
    from flask import redirect, url_for
    return redirect(url_for('formations.index'))


@blueprint.route('/api/stats')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_stats():
    from app.models import Reclamation, Fournisseur, Formation, Equipement, ControleQualite, RevueDirection
    from app.models.nonconformite import NonConformite
    eid = current_user.entreprise_id
    return jsonify({
        'risques': Risque.query.filter_by(entreprise_id=eid).count(),
        'reclamations': Reclamation.query.filter_by(entreprise_id=eid).count(),
        'fournisseurs': Fournisseur.query.filter_by(entreprise_id=eid).count(),
        'formations': Formation.query.filter_by(entreprise_id=eid).count(),
        'equipements': Equipement.query.filter_by(entreprise_id=eid).count(),
        'controles': ControleQualite.query.filter_by(entreprise_id=eid).count(),
        'revues': RevueDirection.query.filter_by(entreprise_id=eid).count(),
        'nonconformites': NonConformite.query.filter_by(entreprise_id=eid, domaine='qualite').count(),
    })


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
        'niveau_risque': r.niveau_risque,
        'maitrise': r.maitrise,
        'statut': r.statut,
        'categorie': r.categorie,
        'processus_concerne': r.processus_concerne,
        'plan_traitement': r.plan_traitement,
        'action_preventive': r.action_preventive,
        'responsable': f'{r.responsable.prenom} {r.responsable.nom}' if r.responsable else '',
        'responsable_id': r.responsable_id,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
        'date_prochaine_revu': r.date_prochaine_revu.isoformat() if r.date_prochaine_revu else None,
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
        categorie=data.get('categorie'),
        processus_concerne=data.get('processus_concerne'),
        plan_traitement=data.get('plan_traitement'),
        action_preventive=data.get('action_preventive'),
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
    item.categorie = data.get('categorie', item.categorie)
    item.processus_concerne = data.get('processus_concerne', item.processus_concerne)
    item.plan_traitement = data.get('plan_traitement', item.plan_traitement)
    item.action_preventive = data.get('action_preventive', item.action_preventive)
    if data.get('date_prochaine_revu'):
        item.date_prochaine_revu = datetime.strptime(data['date_prochaine_revu'], '%Y-%m-%d').date()
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


@blueprint.route('/api/risques/heatmap')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_heatmap():
    items = Risque.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    grid = [[0]*5 for _ in range(5)]
    for r in items:
        g = min(r.gravite, 5) - 1
        p = min(r.probabilite, 5) - 1
        grid[g][p] += 1
    return jsonify({'grid': grid, 'total': len(items)})


@blueprint.route('/api/risques/stats')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_stats():
    eid = current_user.entreprise_id
    items = Risque.query.filter_by(entreprise_id=eid).all()
    par_niveau = {'faible': 0, 'moyen': 0, 'eleve': 0, 'critique': 0}
    for r in items:
        par_niveau[r.niveau_risque] = par_niveau.get(r.niveau_risque, 0) + 1
    par_statut = {}
    for r in items:
        par_statut[r.statut] = par_statut.get(r.statut, 0) + 1
    return jsonify({
        'total': len(items),
        'par_niveau': par_niveau,
        'par_statut': par_statut,
    })


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
