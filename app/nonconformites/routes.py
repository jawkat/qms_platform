from flask import render_template, request, abort
from flask_login import login_required, current_user
from app.utils.permissions import has_permission
from app import db
from app.nonconformites import blueprint
from app.models.nonconformite import NonConformite
from app.schemas.nonconformite import NonConformiteSchema, NonConformiteCreateSchema, NonConformiteUpdateSchema
from sqlalchemy import func
from datetime import date, datetime


@blueprint.route('/')
@login_required
@has_permission('nonconformites.voir')
def index():
    return render_template('nonconformites/index.html')


@blueprint.get('/api/liste')
@login_required
@has_permission('nonconformites.voir')
def api_liste():
    """Liste des non-conformités filtrée"""
    eid = current_user.entreprise_id
    q = NonConformite.query.filter_by(entreprise_id=eid)

    domaine = request.args.get('domaine')
    if domaine:
        q = q.filter_by(domaine=domaine)

    statut = request.args.get('statut')
    if statut:
        q = q.filter_by(statut=statut)

    gravite = request.args.get('gravite')
    if gravite:
        q = q.filter_by(gravite=gravite)

    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                NonConformite.reference.ilike(like),
                NonConformite.description.ilike(like),
            )
        )

    return q.order_by(NonConformite.date_creation.desc()).all()


@blueprint.post('/api/creer')
@login_required
@has_permission('nonconformites.gerer')
@blueprint.arguments(NonConformiteCreateSchema)
@blueprint.response(201, NonConformiteSchema)
def api_creer(data):
    """Créer une nouvelle non-conformité"""
    data.entreprise_id = current_user.entreprise_id
    db.session.add(data)
    db.session.commit()
    return data


@blueprint.post('/api/<int:item_id>/modifier')
@login_required
@has_permission('nonconformites.gerer')
@blueprint.arguments(NonConformiteUpdateSchema)
@blueprint.response(200, NonConformiteSchema)
def api_modifier(data, item_id):
    """Mettre à jour une non-conformité"""
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    
    # Update fields from data (data is already a partial model instance thanks to load_instance=True)
    # But for partial updates with load_instance, smorest/marshmallow-sqlalchemy 
    # usually merges into the existing instance if we provide it to the schema.
    # Here Smorest provides the loaded data objects.
    
    for field, value in request.get_json().items():
        if hasattr(item, field) and field not in ('id', 'entreprise_id', 'date_creation'):
             setattr(item, field, value)
             
    db.session.commit()
    return item


@blueprint.post('/api/<int:item_id>/supprimer')
@login_required
@has_permission('nonconformites.gerer')
def api_supprimer(item_id):
    """Supprimer une non-conformité"""
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return {'success': True}


@blueprint.post('/api/<int:item_id>/valider-cloture')
@login_required
@has_permission('nonconformites.valider_cloture')
@blueprint.response(200, NonConformiteSchema)
def api_valider_cloture(item_id):
    """Valider la clôture d'une non-conformité"""
    item = NonConformite.query.filter_by(id=item_id, entreprise_id=current_user.entreprise_id).first_or_404()
    item.statut = 'cloturee'
    item.valitee_par_id = current_user.id
    item.date_validation_cloture = date.today()
    item.cloture_le = date.today()
    db.session.commit()
    return item


@blueprint.get('/api/stats')
@login_required
@has_permission('nonconformites.voir')
def api_stats():
    """Statistiques des non-conformités"""
    eid = current_user.entreprise_id
    base = NonConformite.query.filter_by(entreprise_id=eid)
    return {
        'total': base.count(),
        'ouvertes': base.filter_by(statut='ouverte').count(),
        'en_cours': base.filter_by(statut='en_cours').count(),
        'cloturees': base.filter_by(statut='cloturee').count(),
        'mineur': base.filter_by(gravite='mineur').count(),
        'majeur': base.filter_by(gravite='majeur').count(),
        'critique': base.filter_by(gravite='critique').count(),
        'hse': base.filter_by(domaine='hse').count(),
        'qualite': base.filter_by(domaine='qualite').count(),
        'haccp': base.filter_by(domaine='haccp').count(),
    }
