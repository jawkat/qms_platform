from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db
from app.models import Audit, AuditObservation, Utilisateur, TexteReglementaire, Article
from app.audit import blueprint
from app.schemas.audit import AuditSchema, AuditObservationSchema
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import has_permission
from datetime import datetime
import csv
import io


@blueprint.route('/')
@login_required
@has_permission('audit.voir')
def index():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    q = Audit.query.filter_by(
        domaine=domaine
    )
    type_filter = request.args.get('type')
    resultat = request.args.get('resultat')
    search = request.args.get('search')
    if type_filter:
        q = q.filter(Audit.type == type_filter)
    if resultat:
        q = q.filter(Audit.resultat_global == resultat)
    if search:
        q = q.filter(Audit.commentaire.ilike(f'%{search}%'))
    audits = q.order_by(Audit.date_creation.desc()).all()
    auditeurs = Utilisateur.query.all()
    return render_template('audit/index.html', audits=audits, auditeurs=auditeurs,
                           filters=request.args)


@blueprint.route('/creer', methods=['GET'])
@login_required
def creer():
    return redirect(url_for('audit.index'))


@blueprint.post('/creer')
@login_required
@has_permission('audit.cree')
@blueprint.arguments(AuditSchema)
@blueprint.response(201, AuditSchema)
def api_creer(data):
    """Créer un nouvel audit"""
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    data.entreprise_id = current_user.entreprise_id
    data.domaine = domaine
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.get('/api/liste')
@login_required
@has_permission('audit.voir')
@blueprint.response(200, AuditSchema(many=True))
def api_liste():
    """Liste des audits"""
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    return Audit.query.filter_by(
        domaine=domaine
    ).order_by(Audit.date_creation.desc()).all()


@blueprint.route('/<int:audit_id>', methods=['GET'])
@login_required
@has_permission('audit.voir')
def detail(audit_id):
    audit = tenant_get_or_404(Audit, audit_id)
    auditeurs = Utilisateur.query.all()
    textes = TexteReglementaire.query.order_by(TexteReglementaire.titre).all()
    articles = Article.query.order_by(Article.numero_article).all()
    return render_template('audit/detail.html', audit=audit, auditeurs=auditeurs,
                           textes=textes, articles=articles)


@blueprint.post('/<int:audit_id>/update')
@login_required
@has_permission('audit.modifier')
@blueprint.arguments(AuditSchema(partial=True))
@blueprint.response(200, AuditSchema)
def update(data, audit_id):
    """Mettre à jour un audit"""
    audit = tenant_get_or_404(Audit, audit_id)
    for field, value in request.get_json().items():
        if hasattr(audit, field) and field not in ('id', 'entreprise_id', 'date_creation'):
            setattr(audit, field, value)
    db.session.commit()
    return audit


@blueprint.post('/<int:audit_id>/delete')
@login_required
@has_permission('audit.modifier')
def delete(audit_id):
    """Supprimer un audit"""
    audit = tenant_get_or_404(Audit, audit_id)
    db.session.delete(audit)
    db.session.commit()
    flash('Audit supprimé.', 'success')
    return redirect(url_for('audit.index'))


@blueprint.post('/<int:audit_id>/observation/add')
@login_required
@has_permission('audit.modifier')
@blueprint.arguments(AuditObservationSchema)
@blueprint.response(201, AuditObservationSchema)
def add_observation(data, audit_id):
    """Ajouter une observation à un audit"""
    audit = tenant_get_or_404(Audit, audit_id)
    data.audit_id = audit.id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/<int:audit_id>/observation/<int:obs_id>/delete')
@login_required
@has_permission('audit.modifier')
def delete_observation(audit_id, obs_id):
    """Supprimer une observation"""
    tenant_get_or_404(Audit, audit_id)
    obs = AuditObservation.query.get_or_404(obs_id)
    if obs.audit_id != audit_id:
        from flask import abort
        abort(404)
    db.session.delete(obs)
    db.session.commit()
    return {'success': True}


@blueprint.route('/api/export')
@login_required
@has_permission('audit.voir')
def export_audits():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    audits = Audit.query.filter_by(
        domaine=domaine
    ).order_by(Audit.date_creation.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Type', 'Résultat global', 'Date audit', 'Commentaire', 'Créé le'])
    for a in audits:
        writer.writerow([
            a.id,
            a.type or '',
            a.resultat_global or '',
            a.date_audit.strftime('%d/%m/%Y') if a.date_audit else '',
            a.commentaire or '',
            a.date_creation.strftime('%d/%m/%Y %H:%M') if a.date_creation else '',
        ])

    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=audits_export.csv'}
    )
