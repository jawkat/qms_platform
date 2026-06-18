from app import db
from app.models import SubscriptionPlan


DEFAULT_SUBSCRIPTION_PLANS = {
    'essential': {
        'label': 'Essential',
        'max_users': 2,
        'price_mad': 7900,
        'max_documents': 200,
        'max_open_actions': 80,
        'max_storage_mb': 512,
        'trial_days': 14,
        'features': {'veille': 'de_base', 'email': True, 'export': False},
    },
    'professional': {
        'label': 'Professional',
        'max_users': 10,
        'price_mad': 10900,
        'max_documents': 2000,
        'max_open_actions': 600,
        'max_storage_mb': 5120,
        'trial_days': 14,
        'features': {'veille': 'complete', 'email': True, 'export': True, 'analytics': True},
    },
    'premium': {
        'label': 'Premium',
        'max_users': 20,
        'price_mad': 15000,
        'max_documents': 10000,
        'max_open_actions': 3000,
        'max_storage_mb': 20480,
        'trial_days': 14,
        'features': {'veille': 'complete', 'email': True, 'export': True, 'analytics': True, 'api': True, 'sla': '99.9'},
    },
}


def _seed_default_plans():
    for key, data in DEFAULT_SUBSCRIPTION_PLANS.items():
        existing = SubscriptionPlan.query.filter_by(plan_key=key).first()
        if not existing:
            plan = SubscriptionPlan(plan_key=key, **data)
            db.session.add(plan)
    db.session.commit()


def get_subscription_plan(plan_key):
    if not plan_key:
        return None
    data = DEFAULT_SUBSCRIPTION_PLANS.get(plan_key)
    if data:
        return data
    plan = SubscriptionPlan.query.filter_by(plan_key=plan_key).first()
    if plan:
        return {
            'plan_key': plan.plan_key,
            'label': plan.label,
            'max_users': plan.max_users or 0,
            'price_mad': plan.price_mad or 0,
            'max_documents': plan.max_documents or 0,
            'max_open_actions': plan.max_open_actions or 0,
            'max_storage_mb': plan.max_storage_mb or 0,
            'trial_days': plan.trial_days or 14,
        }
    return None


def get_subscription_quota_limit(plan_key, quota_name):
    plan = get_subscription_plan(plan_key)
    if not plan:
        return None
    mapping = {
        'max_documents': 'max_documents',
        'max_open_actions': 'max_open_actions',
        'max_storage_mb': 'max_storage_mb',
    }
    key = mapping.get(quota_name)
    if key:
        return plan.get(key)
    return None


def get_subscription_user_limit(plan_key):
    plan = get_subscription_plan(plan_key)
    if plan:
        return plan.get('max_users')
    return None
