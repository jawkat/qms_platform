from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app import db, csrf
from app.models import ActionCorrective, ProofMaster, ProofReference, Utilisateur
from app.actions import blueprint
from app.utils.tenant_scope import tenant_get_or_404
from app.utils.permissions import has_permission
from app.services.quota_middleware import check_quota
from app.services.proof_service import ProofService
from datetime import datetime, date
import csv
import io


@blueprint.route('/')
@blueprint.route('/')
@blueprint.route('/liste')
@login_required
@has_permission('actions.voir')
def liste_actions():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    q = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    )
    statut = request.args.get('statut')
    priorite = request.args.get('priorite')
    source = request.args.get('source')
    search = request.args.get('search')
    if statut:
        q = q.filter(ActionCorrective.statut == statut)
    if priorite:
        q = q.filter(ActionCorrective.priorite == priorite)
    if source:
        q = q.filter(ActionCorrective.source_type == source)
    if search:
        q = q.filter(ActionCorrective.description.ilike(f'%{search}%'))
    actions = q.order_by(ActionCorrective.date_creation.desc()).all()
    responsables = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    return render_template('actions/liste.html', actions=actions, responsables=responsables,
                           domaine=domaine, filters=request.args)


@blueprint.route('/api/liste')
@login_required
@has_permission('actions.voir')
def api_liste_actions():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    ).order_by(ActionCorrective.date_creation.desc()).all()
    return jsonify([{
        'id': a.id, 'description': a.description, 'statut': a.statut,
        'statut_label': a.statut_label, 'priorite': a.priorite,
        'date_echeance': a.date_echeance.isoformat() if a.date_echeance else None,
        'responsable': a.responsable.prenom + ' ' + a.responsable.nom if a.responsable else None,
        'responsable_id': a.responsable_id, 'source_type': a.source_type,
        'cause': a.cause_identifiee, 'date_creation': a.date_creation.isoformat() if a.date_creation else None,
    } for a in actions])


@blueprint.route('/api/create', methods=['POST'])
@login_required
@has_permission('actions.cree')
@check_quota('actions')
@csrf.exempt
def api_create_action():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    data = request.get_json()
    action = ActionCorrective(
        entreprise_id=current_user.entreprise_id, domaine=domaine,
        description=data.get('description'),
        type_action=data.get('type_action', 'corrective'),
        priorite=data.get('priorite', 'moyenne'),
        responsable_id=data.get('responsable_id'),
        cause_identifiee=data.get('cause_identifiee'),
        source_type=data.get('source_type'), source_id=data.get('source_id'),
        date_echeance=datetime.strptime(data['date_echeance'], '%Y-%m-%d').date()
        if data.get('date_echeance') else None,
    )
    db.session.add(action)
    db.session.commit()
    return jsonify({'success': True, 'id': action.id})


@blueprint.route('/<int:action_id>', methods=['GET', 'POST'])
@login_required
@has_permission('actions.modifier')
@csrf.exempt
def detail_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    responsables = Utilisateur.query.filter_by(entreprise_id=current_user.entreprise_id).all()
    if request.method == 'POST':
        action.description = request.form.get('description', action.description)
        action.statut = request.form.get('statut', action.statut)
        action.priorite = request.form.get('priorite', action.priorite)
        action.type_action = request.form.get('type_action', action.type_action)
        action.responsable_id = request.form.get('responsable_id', type=int) or action.responsable_id
        action.cause_identifiee = request.form.get('cause_identifiee')
        if request.form.get('date_echeance'):
            action.date_echeance = datetime.strptime(request.form['date_echeance'], '%Y-%m-%d').date()
        action.est_recurrente = bool(request.form.get('est_recurrente'))
        action.frequence = request.form.get('frequence')
        action.efficacite = request.form.get('efficacite', type=float) or None
        action.commentaire_efficacite = request.form.get('commentaire_efficacite')
        action.critere_efficacite = request.form.get('critere_efficacite')
        action.rca_pourquoi1 = request.form.get('rca_pourquoi1')
        action.rca_pourquoi2 = request.form.get('rca_pourquoi2')
        action.rca_pourquoi3 = request.form.get('rca_pourquoi3')
        action.rca_pourquoi4 = request.form.get('rca_pourquoi4')
        action.rca_pourquoi5 = request.form.get('rca_pourquoi5')
        action.rca_conclusion = request.form.get('rca_conclusion')
        if request.form.get('statut') == 'REALISE' and not action.date_realisation:
            action.date_realisation = date.today()
        db.session.commit()
        flash('Action mise a jour.', 'success')
        return redirect(url_for('actions.detail_action', action_id=action.id))
    return render_template('actions/detail.html', action=action, responsables=responsables)


@blueprint.route('/<int:action_id>/api/update', methods=['POST'])
@login_required
@has_permission('actions.modifier')
@csrf.exempt
def api_update_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    data = request.get_json()
    for field in ('description', 'statut', 'priorite', 'type_action', 'cause_identifiee',
                  'commentaire_efficacite', 'critere_efficacite',
                  'rca_pourquoi1', 'rca_pourquoi2', 'rca_pourquoi3',
                  'rca_pourquoi4', 'rca_pourquoi5', 'rca_conclusion', 'frequence'):
        if field in data:
            setattr(action, field, data[field])
    if 'responsable_id' in data:
        action.responsable_id = data['responsable_id']
    if 'efficacite' in data:
        action.efficacite = float(data['efficacite']) if data['efficacite'] else None
    if 'est_recurrente' in data:
        action.est_recurrente = bool(data['est_recurrente'])
    if data.get('statut') == 'REALISE' and not action.date_realisation:
        action.date_realisation = date.today()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/<int:action_id>/status', methods=['POST'])
@login_required
@has_permission('actions.modifier')
@csrf.exempt
def update_status(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    new_status = request.json.get('statut') if request.is_json else request.form.get('statut')
    if new_status:
        action.statut = new_status
        if new_status == 'REALISE':
            action.date_realisation = date.today()
        db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'statut': action.statut_label})
    flash('Statut mis a jour.', 'success')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.route('/<int:action_id>/proof/attach', methods=['POST'])
@login_required
@has_permission('actions.modifier')
@csrf.exempt
def attach_proof(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    proof_id = request.json.get('proof_id') if request.is_json else request.form.get('proof_id')
    if proof_id:
        ref = ProofService.attach_proof(
            entreprise_id=current_user.entreprise_id,
            entity_type='action_corrective', entity_id=action.id,
            proof_id=int(proof_id), attached_by=current_user.id,
        )
        db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'reference_id': ref.id if ref else None})
    flash('Preuve attachee.', 'success')
    return redirect(url_for('actions.detail_action', action_id=action.id))


@blueprint.route('/<int:action_id>/proof/detach/<int:ref_id>', methods=['POST'])
@login_required
@has_permission('actions.modifier')
@csrf.exempt
def detach_proof(action_id, ref_id):
    ref = tenant_get_or_404(ProofReference, ref_id)
    ProofService.detach_proof(ref.proof_master_id, ref.entity_type, ref.entity_id)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/<int:action_id>/proof/liste')
@login_required
@has_permission('actions.modifier')
def list_proofs(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    refs = ProofReference.query.filter_by(
        entity_type='action_corrective', entity_id=action.id
    ).all()
    return jsonify([{
        'id': r.id, 'proof_id': r.proof_master_id,
        'nom_fichier': r.proof_master.nom_fichier if r.proof_master else '?',
        'date_attached': r.date_attached.isoformat() if r.date_attached else None,
    } for r in refs])


@blueprint.route('/<int:action_id>/delete', methods=['POST'])
@login_required
@has_permission('actions.supprimer')
@csrf.exempt
def delete_action(action_id):
    action = tenant_get_or_404(ActionCorrective, action_id)
    db.session.delete(action)
    db.session.commit()
    flash('Action supprimee.', 'success')
    return redirect(url_for('actions.liste_actions'))


@blueprint.route('/api/export')
@login_required
@has_permission('actions.voir')
def export_actions():
    domaine = __import__('flask').session.get('domaine_actif', 'hse')
    actions = ActionCorrective.query.filter_by(
        entreprise_id=current_user.entreprise_id, domaine=domaine
    ).order_by(ActionCorrective.date_creation.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Description', 'Type', 'Priorité', 'Statut', 'Responsable', 'Échéance', 'Créé le'])
    for a in actions:
        writer.writerow([
            a.id,
            a.description or '',
            a.type_action or '',
            a.priorite or '',
            a.statut_label,
            f'{a.responsable.prenom} {a.responsable.nom}' if a.responsable else '',
            a.date_echeance.strftime('%d/%m/%Y') if a.date_echeance else '',
            a.date_creation.strftime('%d/%m/%Y %H:%M') if a.date_creation else '',
        ])

    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=actions_export.csv'}
    )
