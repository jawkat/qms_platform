from flask import render_template, request
from flask_login import current_user
from app import db
from app.indicateurs import blueprint
from app.models.indicateurs import Indicateur, IndicateurValeur
from app.schemas.indicateurs import IndicateurSchema, IndicateurValeurSchema
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from datetime import datetime, date


class IndicateurResource(BaseResource):
    model = Indicateur
    schema = None
    protected_fields = frozenset({'id', 'entreprise_id', 'date_creation'})


class IndicateurValeurResource(BaseResource):
    model = IndicateurValeur
    schema = None
    protected_fields = frozenset({'id', 'indicateur_id', 'date_calcul'})


@blueprint.route('/')
@access_required(permission='indicateurs.voir')
def index():
    q = Indicateur.query.order_by(Indicateur.nom)
    periode_filter = request.args.get('periode')
    if periode_filter:
        q = q.filter(Indicateur.periode == periode_filter)
    indicateurs = q.all()
    periodes = db.session.query(Indicateur.periode).distinct().all()
    periodes = sorted(set(p[0] for p in periodes if p[0]))

    cards = []
    for ind in indicateurs:
        valeurs = IndicateurValeur.query.filter_by(
            indicateur_id=ind.id
        ).order_by(IndicateurValeur.date_calcul.desc()).all()
        derniere = valeurs[0] if valeurs else None
        avant = valeurs[1] if len(valeurs) > 1 else None
        tendance = None
        if derniere and avant and avant.valeur != 0:
            tendance = round(((derniere.valeur - avant.valeur) / abs(avant.valeur)) * 100, 1)
        cards.append({
            'indicateur': ind,
            'derniere_valeur': derniere.valeur if derniere else None,
            'date_calcul': derniere.date_calcul if derniere else None,
            'tendance': tendance,
        })
    return render_template('indicateurs/index.html', cards=cards,
                           periodes=periodes, filtres={'periode': periode_filter})


@blueprint.route('/<int:indicateur_id>')
@access_required(permission='indicateurs.voir')
def detail(indicateur_id):
    ind = Indicateur.query.get_or_404(indicateur_id)
    valeurs = IndicateurValeur.query.filter_by(
        indicateur_id=ind.id
    ).order_by(IndicateurValeur.date_calcul.desc()).all()
    return render_template('indicateurs/detail.html', indicateur=ind, valeurs=valeurs)


@blueprint.get('/api/liste')
@access_required(permission='indicateurs.voir')
@blueprint.response(200, IndicateurSchema(many=True))
def api_liste():
    """Liste des indicateurs"""
    return Indicateur.query.order_by(Indicateur.nom).all()


@blueprint.post('/api/create')
@access_required(permission='indicateurs.cree')
@blueprint.arguments(IndicateurSchema)
@blueprint.response(201, IndicateurSchema)
def api_create(data):
    return IndicateurResource.create_resource(data)


@blueprint.post('/api/update/<int:item_id>')
@access_required(permission='indicateurs.modifier')
@blueprint.arguments(IndicateurSchema(partial=True))
@blueprint.response(200, IndicateurSchema)
def api_update(data, item_id):
    """Mettre à jour un indicateur"""
    ind = db.session.get(Indicateur, item_id)
    if not ind:
        abort(404)
    for field, value in request.get_json().items():
        if hasattr(ind, field) and field not in ('id', 'date_creation'):
            setattr(ind, field, value)
    db.session.commit()
    return ind


@blueprint.post('/api/delete/<int:item_id>')
@access_required(permission='indicateurs.modifier')
def api_delete(item_id):
    """Supprimer un indicateur"""
    ind = db.session.get(Indicateur, item_id)
    if not ind:
        return {'success': False}, 404
    IndicateurValeur.query.filter_by(indicateur_id=ind.id).delete()
    db.session.delete(ind)
    db.session.commit()
    return {'success': True}


@blueprint.post('/api/valeur/add')
@access_required(permission='indicateurs.modifier')
@blueprint.arguments(IndicateurValeurSchema)
@blueprint.response(201, IndicateurValeurSchema)
def api_valeur_add(data):
    return IndicateurValeurResource.create_resource(data)
