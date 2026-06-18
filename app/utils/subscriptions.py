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
