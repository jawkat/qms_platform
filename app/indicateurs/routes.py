from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.indicateurs import blueprint
from app.models.indicateurs import Indicateur, IndicateurValeur
from app.utils.permissions import has_permission
from datetime import datetime, date


@blueprint.route('/')
@login_required
@has_permission('indicateurs.voir')
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
            indicateur_id=ind.id, entreprise_id=current_user.entreprise_id
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
@login_required
@has_permission('indicateurs.voir')
def detail(indicateur_id):
    ind = Indicateur.query.get_or_404(indicateur_id)
    valeurs = IndicateurValeur.query.filter_by(
        indicateur_id=ind.id, entreprise_id=current_user.entreprise_id
    ).order_by(IndicateurValeur.date_calcul.desc()).all()
    return render_template('indicateurs/detail.html', indicateur=ind, valeurs=valeurs)


@blueprint.route('/api/liste')
@login_required
@has_permission('indicateurs.voir')
def api_liste():
    indicateurs = Indicateur.query.order_by(Indicateur.nom).all()
    result = []
    for ind in indicateurs:
        valeurs = IndicateurValeur.query.filter_by(
            indicateur_id=ind.id, entreprise_id=current_user.entreprise_id
        ).order_by(IndicateurValeur.date_calcul.desc()).limit(2).all()
        derniere = valeurs[0] if valeurs else None
        avant = valeurs[1] if len(valeurs) > 1 else None
        tendance = None
        if derniere and avant and avant.valeur != 0:
            tendance = round(((derniere.valeur - avant.valeur) / abs(avant.valeur)) * 100, 1)
        result.append({
            'id': ind.id,
            'nom': ind.nom,
            'description': ind.description,
            'formule': ind.formule,
            'periode': ind.periode,
            'calcul_auto': ind.calcul_auto,
            'date_creation': ind.date_creation.isoformat() if ind.date_creation else None,
            'derniere_valeur': {
                'valeur': derniere.valeur if derniere else None,
                'date_calcul': derniere.date_calcul.isoformat() if derniere else None,
                'tendance': tendance,
            } if derniere else None,
        })
    return jsonify(result)


@blueprint.route('/api/create', methods=['POST'])
@login_required
@has_permission('indicateurs.cree')
def api_create():
    data = request.get_json()
    ind = Indicateur(
        nom=data.get('nom'),
        description=data.get('description'),
        formule=data.get('formule'),
        periode=data.get('periode'),
        calcul_auto=bool(data.get('calcul_auto')),
    )
    db.session.add(ind)
    db.session.commit()
    return jsonify({'success': True, 'id': ind.id})


@blueprint.route('/api/update/<int:id>', methods=['POST'])
@login_required
@has_permission('indicateurs.modifier')
def api_update(id):
    ind = db.session.get(Indicateur, id)
    if not ind:
        return jsonify({'success': False, 'erreur': 'Indicateur introuvable'}), 404
    data = request.get_json()
    for field in ('nom', 'description', 'formule', 'periode'):
        if field in data:
            setattr(ind, field, data[field])
    if 'calcul_auto' in data:
        ind.calcul_auto = bool(data['calcul_auto'])
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/delete/<int:id>', methods=['POST'])
@login_required
@has_permission('indicateurs.modifier')
def api_delete(id):
    ind = db.session.get(Indicateur, id)
    if not ind:
        return jsonify({'success': False, 'erreur': 'Indicateur introuvable'}), 404
    IndicateurValeur.query.filter_by(indicateur_id=ind.id).delete()
    db.session.delete(ind)
    db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/api/valeur/add', methods=['POST'])
@login_required
@has_permission('indicateurs.modifier')
def api_valeur_add():
    data = request.get_json()
    indicateur = db.session.get(Indicateur, data.get('indicateur_id'))
    if not indicateur:
        return jsonify({'success': False, 'erreur': 'Indicateur introuvable'}), 404
    try:
        d = datetime.strptime(data['date_calcul'], '%Y-%m-%d').date()
    except (KeyError, ValueError):
        return jsonify({'success': False, 'erreur': 'date_calcul invalide (YYYY-MM-DD)'}), 400
    try:
        v = float(data['valeur'])
    except (KeyError, ValueError):
        return jsonify({'success': False, 'erreur': 'valeur invalide'}), 400
    val = IndicateurValeur(
        indicateur_id=indicateur.id,
        entreprise_id=current_user.entreprise_id,
        date_calcul=d,
        valeur=v,
    )
    db.session.add(val)
    db.session.commit()
    return jsonify({'success': True, 'id': val.id})
