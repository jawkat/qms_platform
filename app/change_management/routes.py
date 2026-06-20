from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.change_management import blueprint
from app.models import ChangeRequest
from app.models.auth import Utilisateur
from datetime import date, datetime


@blueprint.route('/')
@login_required
@has_permission('change_management.voir')
def index():
    utilisateurs = Utilisateur.query.filter_by(
        entreprise_id=current_user.entreprise_id, actif=True
    ).order_by(Utilisateur.nom).all()
    return render_template('change_management/index.html', utilisateurs=utilisateurs)


@blueprint.route('/api/liste')
@login_required
@has_permission('change_management.voir')
def api_liste():
    items = ChangeRequest.query.filter_by(
        entreprise_id=current_user.entreprise_id
    ).order_by(ChangeRequest.date_creation.desc()).all()
    return jsonify([{
        'id': r.id, 'reference': r.reference, 'titre': r.titre,
        'description': r.description, 'type_changement': r.type_changement,
        'priorite': r.priorite, 'statut': r.statut,
        'demandeur': f'{r.demandeur.prenom} {r.demandeur.nom}' if r.demandeur else '',
        'date_demande': r.date_demande.isoformat() if r.date_demande else None,
        'date_souhaitee': r.date_souhaitee.isoformat() if r.date_souhaitee else None,
        'raison': r.raison,
        'impact_description': r.impact_description,
        'impact_secteurs': r.impact_secteurs,
        'risques_identifies': r.risques_identifies,
        'approbateur': f'{r.approbateur.prenom} {r.approbateur.nom}' if r.approbateur else '',
        'date_approbation': r.date_approbation.isoformat() if r.date_approbation else None,
        'commentaire_approbation': r.commentaire_approbation,
        'date_creation': r.date_creation.isoformat() if r.date_creation else None,
    } for r in items])


@blueprint.route('/api/stats')
@login_required
@has_permission('change_management.voir')
def api_stats():
    eid = current_user.entreprise_id
    base = ChangeRequest.query.filter_by(entreprise_id=eid)
    return jsonify({
        'total': base.count(),
        'brouillon': base.filter_by(statut='brouillon').count(),
        'soumis': base.filter_by(statut='soumis').count(),
        'approuve': base.filter_by(statut='approuve').count(),
        'en_realisation': base.filter_by(statut='en_realisation').count(),
        'cloture': base.filter_by(statut='cloture').count(),
        'rejete': base.filter_by(statut='rejete').count(),
    })


@blueprint.route('/api/creer', methods=['POST'])
@login_required
@has_permission('change_management.gerer')
def api_creer():
    data = request.get_json()
    item = ChangeRequest(
        entreprise_id=current_user.entreprise_id,
        titre=data.get('titre'), description=data.get('description'),
        type_changement=data.get('type_changement', 'processus'),
        priorite=data.get('priorite', 'moyenne'),
        statut=data.get('statut', 'brouillon'),
        demandeur_id=current_user.id,
        date_demande=datetime.strptime(data['date_demande'], '%Y-%m-%d').date()
        if data.get('date_demande') else date.today(),
        date_souhaitee=datetime.strptime(data['date_souhaitee'], '%Y-%m-%d').date()
        if data.get('date_souhaitee') else None,
        raison=data.get('raison'),
        impact_description=data.get('impact_description'),
        impact_secteurs=data.get('impact_secteurs'),
        risques_identifies=data.get('risques_identifies'),
    )
    item.reference = item.generate_reference()
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'id': item.id, 'reference': item.reference})


@blueprint.route('/api/<int:item_id>/modifier', methods=['POST'])
@login_required
@has_permission('change_management.gerer')
def api_modifier(item_id):
    item = ChangeRequest.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    data = request.get_json()
    for f in ('titre', 'description', 'type_changement', 'priorite', 'statut',
              'raison', 'impact_description', 'impact_secteurs', 'impact_utilisateurs',
              'impact_documents', 'impact_delai', 'impact_cout',
              'risques_identifies', 'mesures_mitigation', 'commentaire_approbation'):
        if f in data:
            setattr(item, f, data[f])
    if data.get('date_souhaitee'):
        item.date_souhaitee = datetime.strptime(data['date_souhaitee'], '%Y-%m-%d').date()
    if data.get('approbateur_id'):
        item.approbateur_id = data['approbateur_id']
        item.date_approbation = datetime.utcnow()
    if data.get('date_realisation'):
        item.date_realisation = datetime.strptime(data['date_realisation'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/<int:item_id>/supprimer', methods=['POST'])
@login_required
@has_permission('change_management.gerer')
def api_supprimer(item_id):
    item = ChangeRequest.query.filter_by(
        id=item_id, entreprise_id=current_user.entreprise_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
