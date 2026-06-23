from flask import render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import current_user
from app import db
from app.models import Entreprise, SubscriptionPlan
from app.plans import plans
from app.utils.subscriptions import get_subscription_plan
from app.utils.permissions import access_required
from app.utils.base_resource import BaseResource
from datetime import datetime


class SubscriptionPlanResource(BaseResource):
    model = SubscriptionPlan
    protected_fields = frozenset({'id', 'date_creation'})


# --- Pages ---

@plans.route('/')
@access_required()
def index():
    plans_list = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return render_template('plans/index.html', plans=plans_list)


@plans.route('/create', methods=['GET', 'POST'])
@access_required(permission='plans.gerer')
def create():
    if request.method == 'POST':
        p = SubscriptionPlan(
            plan_key=request.form['plan_key'],
            label=request.form['label'],
            max_users=int(request.form.get('max_users', 2)),
            price_mad=int(request.form.get('price_mad', 0)),
            max_documents=int(request.form.get('max_documents', 200)),
            max_open_actions=int(request.form.get('max_open_actions', 80)),
            max_storage_mb=int(request.form.get('max_storage_mb', 512)),
            trial_days=int(request.form.get('trial_days', 14)),
            features=request.form.get('features', '{}'),
            is_active=bool(request.form.get('is_active')),
        )
        db.session.add(p)
        db.session.commit()
        flash('Plan créé avec succès.', 'success')
        return redirect(url_for('plans.index'))
    return render_template('plans/create.html')


@plans.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@access_required(permission='plans.gerer')
def edit(plan_id):
    p = db.session.get(SubscriptionPlan, plan_id)
    if not p:
        abort(404)
    if request.method == 'POST':
        p.plan_key = request.form.get('plan_key', p.plan_key)
        p.label = request.form.get('label', p.label)
        p.max_users = int(request.form.get('max_users', p.max_users))
        p.price_mad = int(request.form.get('price_mad', p.price_mad))
        p.max_documents = int(request.form.get('max_documents', p.max_documents))
        p.max_open_actions = int(request.form.get('max_open_actions', p.max_open_actions))
        p.max_storage_mb = int(request.form.get('max_storage_mb', p.max_storage_mb))
        p.trial_days = int(request.form.get('trial_days', p.trial_days))
        p.features = request.form.get('features', p.features)
        p.is_active = bool(request.form.get('is_active'))
        db.session.commit()
        flash('Plan mis à jour.', 'success')
        return redirect(url_for('plans.index'))
    return render_template('plans/edit.html', plan=p)


# --- API ---

@plans.route('/api/plans')
@access_required()
def api_plans():
    plans_list = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    return jsonify([{
        'id': r.id,
        'plan_key': r.plan_key,
        'label': r.label,
        'max_users': r.max_users,
        'price_mad': r.price_mad,
        'max_documents': r.max_documents,
        'max_open_actions': r.max_open_actions,
        'max_storage_mb': r.max_storage_mb,
        'trial_days': r.trial_days,
        'features': r.features,
        'is_active': r.is_active,
    } for r in plans_list])


@plans.route('/api/<int:item_id>/detail')
@access_required()
def api_detail(item_id):
    p = db.session.get(SubscriptionPlan, item_id)
    if not p:
        abort(404)
    return jsonify({
        'id': p.id,
        'plan_key': p.plan_key,
        'label': p.label,
        'max_users': p.max_users,
        'price_mad': p.price_mad,
        'max_documents': p.max_documents,
        'max_open_actions': p.max_open_actions,
        'max_storage_mb': p.max_storage_mb,
        'trial_days': p.trial_days,
        'features': p.features,
        'is_active': p.is_active,
    })


@plans.route('/api/current')
@access_required(permission='plans.voir')
def api_current():
    e = db.session.get(Entreprise, current_user.entreprise_id)
    if not e:
        abort(404)
    plan = SubscriptionPlan.query.filter_by(plan_key=e.abonnement_type).first()
    if not plan:
        return jsonify({'plan_key': e.abonnement_type, 'label': e.abonnement_type})
    return jsonify({
        'plan_key': plan.plan_key,
        'label': plan.label,
        'max_users': plan.max_users,
        'price_mad': plan.price_mad,
        'max_documents': plan.max_documents,
        'max_open_actions': plan.max_open_actions,
        'max_storage_mb': plan.max_storage_mb,
        'trial_days': plan.trial_days,
        'features': plan.features,
        'is_active': plan.is_active,
        'prochaine_echeance': e.abonnement_prochaine_echeance.isoformat() if e.abonnement_prochaine_echeance else None,
        'statut': e.statut,
        'abonnement_paye': e.abonnement_paye,
    })


@plans.route('/api/create', methods=['POST'])
@access_required(permission='plans.gerer')
def api_create():
    data = request.get_json()
    p = SubscriptionPlan(
        plan_key=data.get('plan_key'),
        label=data.get('label'),
        max_users=data.get('max_users', 2),
        price_mad=data.get('price_mad', 0),
        max_documents=data.get('max_documents', 200),
        max_open_actions=data.get('max_open_actions', 80),
        max_storage_mb=data.get('max_storage_mb', 512),
        trial_days=data.get('trial_days', 14),
        features=data.get('features', {}),
        is_active=data.get('is_active', True),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'success': True, 'id': p.id})


@plans.route('/api/<int:id>/update', methods=['POST'])
@access_required(permission='plans.gerer')
def api_update(id):
    p = SubscriptionPlan.query.get_or_404(id)
    data = request.get_json()
    for f in ('plan_key', 'label', 'max_users', 'price_mad', 'max_documents',
              'max_open_actions', 'max_storage_mb', 'trial_days'):
        if f in data and data[f] is not None:
            setattr(p, f, data[f])
    if 'features' in data and data['features'] is not None:
        existing = dict(p.features) if p.features else {}
        if isinstance(data['features'], dict):
            existing.update(data['features'])
            existing = {k: v for k, v in existing.items() if v is not None and v != ''}
        else:
            existing = data['features']
        p.features = dict(existing)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(p, 'features')
    if 'is_active' in data:
        p.is_active = data['is_active']
    db.session.commit()
    return jsonify({'success': True})


@plans.route('/api/<int:id>/delete', methods=['POST'])
@access_required(permission='plans.gerer')
def api_delete(id):
    return jsonify(SubscriptionPlanResource.delete_resource(id))
