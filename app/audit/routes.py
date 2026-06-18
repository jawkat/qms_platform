from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db, csrf
from app.models import Audit, AuditObservation, Utilisateur, TexteReglementaire, Article
from app.audit import blueprint
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
        entreprise_id=current_user.entreprise_id, domaine=domaine
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
    auditeurs = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    return render_template('audit/index.html', audits=audits, auditeurs=auditeurs,
                           filters=request.args)


@blueprint.route('/creer', methods=['GET'])
@login_required
def creer():
    return redirect(url_for('audit.index'))


@blueprint.route('/creer', methods=['POST'])
@login_required
@has_permission('audit.cree')
@csrf.exempt
def api_creer():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    data = request.get_json()
    audit = Audit(
        entreprise_id=current_user.entreprise_id, domaine=domaine,
        type=data.get('type'),
        date_audit=datetime.strptime(data['date_audit'], '%Y-%m-%d').date()
        if data.get('date_audit') else None,
        auditeur_id=data.get('auditeur_id', type=int),
        commentaire=data.get('commentaire'),
    )
    db.session.add(audit)
    db.session.commit()
    return jsonify({'success': True, 'id': audit.id})


@blueprint.route('/api/liste')
@login_required
@has_permission('audit.voir')
def api_liste():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    audits = Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    ).order_by(Audit.date_creation.desc()).all()
    return jsonify([{
        'id': a.id,
        'type': a.type,
        'date_audit': a.date_audit.isoformat() if a.date_audit else None,
        'date_creation': a.date_creation.isoformat() if a.date_creation else None,
        'auditeur': f'{a.auditeur.prenom} {a.auditeur.nom}' if a.auditeur else None,
        'auditeur_id': a.auditeur_id,
        'resultat_global': a.resultat_global,
        'commentaire': a.commentaire,
    } for a in audits])


@blueprint.route('/<int:audit_id>', methods=['GET'])
@login_required
@has_permission('audit.voir')
def detail(audit_id):
    audit = tenant_get_or_404(Audit, audit_id)
    auditeurs = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    textes = TexteReglementaire.query.order_by(TexteReglementaire.titre).all()
    articles = Article.query.order_by(Article.numero_article).all()
    return render_template('audit/detail.html', audit=audit, auditeurs=auditeurs,
                           textes=textes, articles=articles)


@blueprint.route('/<int:audit_id>/update', methods=['POST'])
@login_required
@has_permission('audit.modifier')
@csrf.exempt
def update(audit_id):
    audit = tenant_get_or_404(Audit, audit_id)
    data = request.get_json() if request.is_json else request.form
    if data.get('resultat_global') is not None:
        audit.resultat_global = data['resultat_global']
    if data.get('commentaire') is not None:
        audit.commentaire = data['commentaire']
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True})
    flash('Audit mis à jour.', 'success')
    return redirect(url_for('audit.detail', audit_id=audit.id))


@blueprint.route('/<int:audit_id>/delete', methods=['POST'])
@login_required
@has_permission('audit.modifier')
@csrf.exempt
def delete(audit_id):
    audit = tenant_get_or_404(Audit, audit_id)
    db.session.delete(audit)
    db.session.commit()
    flash('Audit supprimé.', 'success')
    return redirect(url_for('audit.index'))


@blueprint.route('/<int:audit_id>/observation/add', methods=['POST'])
@login_required
@has_permission('audit.modifier')
@csrf.exempt
def add_observation(audit_id):
    audit = tenant_get_or_404(Audit, audit_id)
    data = request.get_json()
    obs = AuditObservation(
        audit_id=audit.id,
        texte_id=data.get('texte_id', type=int),
        article_id=data.get('article_id', type=int),
        constat=data.get('constat'),
        niveau_conformite=data.get('niveau_conformite'),
        action_recommandee=data.get('action_recommandee'),
    )
    db.session.add(obs)
    db.session.commit()
    return jsonify({'success': True, 'id': obs.id})


@blueprint.route('/<int:audit_id>/observation/<int:obs_id>/delete', methods=['POST'])
@login_required
@has_permission('audit.modifier')
@csrf.exempt
def delete_observation(audit_id, obs_id):
    tenant_get_or_404(Audit, audit_id)
    obs = AuditObservation.query.get_or_404(obs_id)
    if obs.audit_id != audit_id:
        from flask import abort
        abort(404)
    db.session.delete(obs)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/export')
@login_required
@has_permission('audit.voir')
def export_audits():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    audits = Audit.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
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
