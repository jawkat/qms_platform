from flask import render_template, request, Response
from flask_login import login_required, current_user
from app.utils.permissions import module_access_required
from app import db
from app.models import Risque
from app.qualite import blueprint
from app.schemas.qualite import RisqueSchema
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


@blueprint.get('/api/stats')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_stats():
    """Statistiques globales qualité"""
    from app.models import Reclamation, Fournisseur, Formation, Equipement, ControleQualite, RevueDirection
    from app.models.nonconformite import NonConformite
    return {
        'risques': Risque.query.count(),
        'reclamations': Reclamation.query.count(),
        'fournisseurs': Fournisseur.query.count(),
        'formations': Formation.query.count(),
        'equipements': Equipement.query.count(),
        'controles': ControleQualite.query.count(),
        'revues': RevueDirection.query.count(),
        'nonconformites': NonConformite.query.filter_by(domaine='qualite').count(),
    }


@blueprint.get('/api/risques')
@login_required
@module_access_required('qualite', 'qualite.voir')
@blueprint.response(200, RisqueSchema(many=True))
def api_risques():
    """Liste des risques qualité"""
    return Risque.query\
        .order_by(Risque.date_creation.desc()).all()


@blueprint.post('/api/risques/create')
@login_required
@module_access_required('qualite', 'qualite.voir')
@blueprint.arguments(RisqueSchema)
@blueprint.response(201, RisqueSchema)
def api_risques_create(data):
    """Créer un nouveau risque"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/risques/<int:item_id>/update')
@login_required
@module_access_required('qualite', 'qualite.voir')
@blueprint.arguments(RisqueSchema(partial=True))
@blueprint.response(200, RisqueSchema)
def api_risques_update(data, item_id):
    """Mettre à jour un risque"""
    item = Risque.query.filter_by(id=item_id).first_or_404()
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(item, field, value)
    db.session.commit()
    return item


@blueprint.post('/api/risques/<int:item_id>/delete')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_delete(item_id):
    """Supprimer un risque"""
    item = Risque.query.filter_by(id=item_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.get('/api/risques/heatmap')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_heatmap():
    """Matrice de criticité des risques"""
    items = Risque.query.all()
    grid = [[0]*5 for _ in range(5)]
    for r in items:
        g = min(r.gravite if r.gravite else 1, 5) - 1
        p = min(r.probabilite if r.probabilite else 1, 5) - 1
        grid[g][p] += 1
    return {'grid': grid, 'total': len(items)}


@blueprint.get('/api/risques/stats')
@login_required
@module_access_required('qualite', 'qualite.voir')
def api_risques_stats():
    """Statistiques par niveau et statut"""
    items = Risque.query.all()
    par_niveau = {'faible': 0, 'moyen': 0, 'eleve': 0, 'critique': 0}
    for r in items:
        par_niveau[r.niveau_risque] = par_niveau.get(r.niveau_risque, 0) + 1
    par_statut = {}
    for r in items:
        par_statut[r.statut] = par_statut.get(r.statut, 0) + 1
    return {
        'total': len(items),
        'par_niveau': par_niveau,
        'par_statut': par_statut,
    }


@blueprint.get('/api/risques/export')
@login_required
@module_access_required('qualite', 'qualite.voir')
def export_risques():
    """Export des risques en CSV"""
    risques_list = Risque.query\
        .order_by(Risque.date_creation.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Désignation', 'Cause', 'Effet', 'Gravité', 'Probabilité', 'Détection', 'IPR', 'Maîtrise', 'Statut', 'Créé le'])
    for r in risques_list:
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
