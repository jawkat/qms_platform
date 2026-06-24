from flask import render_template, request, redirect, url_for, flash, Response
from flask_login import current_user
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from app.services.audit_service import AuditService
from app import db
from app.models import Audit, AuditObservation, Utilisateur, TexteReglementaire, Article
from app.audit import blueprint
from app.schemas.audit import AuditSchema, AuditObservationSchema
from datetime import datetime
from flask import session
import csv
import io


class AuditResource(BaseResource):
    model = Audit
    schema = AuditSchema
    service_class = AuditService
    search_fields = ['commentaire', 'type']

    @classmethod
    def create_resource(cls, data):
        data.entreprise_id = current_user.entreprise_id
        return super().create_resource(data)


@blueprint.post('/creer')
@access_required(permission='audit.modifier')
@blueprint.arguments(AuditSchema)
@blueprint.response(201, AuditSchema)
def api_creer(data):
    """Creer un nouvel audit"""
    return AuditResource.create_resource(data)


@blueprint.get('/api/liste')
@access_required(permission='audit.voir')
@blueprint.response(200, AuditSchema(many=True))
def api_liste():
    """Liste des audits"""
    return Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(Audit.date_creation.desc()).all()


@blueprint.route('/')
@access_required(permission='audit.voir')
def index():
    q = Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id
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
@access_required(permission='audit.voir')
def creer():
    return redirect(url_for('audit.index'))


@blueprint.route('/<int:audit_id>', methods=['GET'])
@access_required(permission='audit.voir')
def detail(audit_id):
    audit = AuditResource.get_resource(audit_id)
    auditeurs = Utilisateur.query.all()
    textes = TexteReglementaire.query.order_by(TexteReglementaire.titre).all()
    articles = Article.query.order_by(Article.numero_article).all()
    return render_template('audit/detail.html', audit=audit, auditeurs=auditeurs,
                           textes=textes, articles=articles)


@blueprint.post('/<int:audit_id>/update')
@access_required(permission='audit.modifier')
@blueprint.arguments(AuditSchema(partial=True))
@blueprint.response(200, AuditSchema)
def update(data, audit_id):
    """Mettre à jour un audit"""
    return AuditResource.update_resource(audit_id)


@blueprint.post('/<int:audit_id>/delete')
@access_required(permission='audit.modifier')
def delete(audit_id):
    """Supprimer un audit"""
    AuditResource.delete_resource(audit_id)
    flash('Audit supprimé.', 'success')
    return redirect(url_for('audit.index'))


@blueprint.post('/<int:audit_id>/observation/add')
@access_required(permission='audit.modifier')
@blueprint.arguments(AuditObservationSchema)
@blueprint.response(201, AuditObservationSchema)
def add_observation(data, audit_id):
    """Ajouter une observation à un audit"""
    audit = AuditResource.get_resource(audit_id)
    data.audit_id = audit.id
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/<int:audit_id>/observation/<int:obs_id>/delete')
@access_required(permission='audit.modifier')
def delete_observation(audit_id, obs_id):
    """Supprimer une observation"""
    AuditResource.get_resource(audit_id)
    obs = AuditObservation.query.get_or_404(obs_id)
    if obs.audit_id != audit_id:
        from flask import abort
        abort(404)
    db.session.delete(obs)
    db.session.commit()
    return {'success': True}


@blueprint.route('/api/export')
@access_required(permission='audit.voir')
def export_audits():
    audits = Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id
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
