import pytest
from datetime import date, timedelta
from app import db
from app.models import Entreprise, Utilisateur, ActionCorrective, ProofMaster
from app.services.subscription_service import (
    get_enterprise_lifecycle_status,
    ensure_enterprise_operation_allowed,
    get_user_limit_status,
    get_action_limit_status,
    get_documents_limit_status,
    get_storage_limit_status,
    parse_optional_date,
    add_one_year_safe,
    get_payment_status,
    get_enterprise_quota_info,
    apply_subscription_update,
)


class TestEnterpriseLifecycleStatus:
    def test_active_status(self, session):
        ent = Entreprise(nom='T', statut='active')
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'active'

    def test_trial_status(self, session):
        ent = Entreprise(nom='T', statut='trial')
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'trial'

    def test_suspended_status(self, session):
        ent = Entreprise(nom='T', statut='suspended')
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'suspended'

    def test_legacy_paid_is_active(self, session):
        ent = Entreprise(nom='T', abonnement_paye=True)
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'active'

    def test_no_statut_no_payment_is_trial(self, session):
        ent = Entreprise(nom='T')
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'trial'

    def test_paid_no_statut_is_active(self, session):
        ent = Entreprise(nom='T', abonnement_paye=True)
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'active'

    def test_trial_expired_is_suspended(self, session):
        ent = Entreprise(nom='T', abonnement_type='trial',
                         abonnement_prochaine_echeance=date.today() - timedelta(days=1))
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'suspended'

    def test_unknown_statut_no_payment_is_trial(self, session):
        ent = Entreprise(nom='T', statut='unknown')
        session.add(ent)
        session.commit()
        assert get_enterprise_lifecycle_status(ent) == 'trial'


class TestEnsureEnterpriseOperationAllowed:
    def test_active_allowed(self, session):
        ent = Entreprise(nom='T', statut='active')
        session.add(ent)
        session.commit()
        allowed, msg, lifecycle = ensure_enterprise_operation_allowed(ent, 'test')
        assert allowed is True
        assert msg is None
        assert lifecycle == 'active'

    def test_suspended_blocked(self, session):
        ent = Entreprise(nom='T', statut='suspended')
        session.add(ent)
        session.commit()
        allowed, msg, lifecycle = ensure_enterprise_operation_allowed(ent, 'create')
        assert allowed is False
        assert 'suspended' in msg
        assert lifecycle == 'suspended'

    def test_cancelled_blocked(self, session):
        ent = Entreprise(nom='T', statut='cancelled')
        session.add(ent)
        session.commit()
        allowed, msg, lifecycle = ensure_enterprise_operation_allowed(ent, 'update')
        assert allowed is False

    def test_archived_blocked(self, session):
        ent = Entreprise(nom='T', statut='archived')
        session.add(ent)
        session.commit()
        allowed, msg, lifecycle = ensure_enterprise_operation_allowed(ent, 'delete')
        assert allowed is False


class TestUserLimitStatus:
    def test_enterprise_not_found(self, session):
        reached, current, limit, plan = get_user_limit_status(9999)
        assert reached is False
        assert current is None

    def test_within_limit(self, session, entreprise):
        reached, current, limit, plan = get_user_limit_status(entreprise.id, extra_users=1)
        assert reached is False
        assert current == 0
        assert limit == 10

    def test_plan_label_returned(self, session, entreprise):
        reached, current, limit, plan = get_user_limit_status(entreprise.id)
        assert plan == 'Professional'


class TestActionLimitStatus:
    def test_enterprise_not_found(self, session):
        reached, current, limit, plan = get_action_limit_status(9999)
        assert reached is False

    def test_within_limit(self, session, entreprise):
        reached, current, limit, plan = get_action_limit_status(entreprise.id)
        assert reached is False
        assert limit == 600


class TestDocumentsLimitStatus:
    def test_enterprise_not_found(self, session):
        reached, current, limit, plan = get_documents_limit_status(9999)
        assert reached is False

    def test_within_limit(self, session, entreprise):
        reached, current, limit, plan = get_documents_limit_status(entreprise.id)
        assert reached is False
        assert limit == 2000


class TestStorageLimitStatus:
    def test_enterprise_not_found(self, session):
        reached, current, limit, plan = get_storage_limit_status(9999)
        assert reached is False


class TestParseOptionalDate:
    def test_valid_date(self):
        result = parse_optional_date('2025-01-15', 'test')
        assert result == date(2025, 1, 15)

    def test_empty_string(self):
        result = parse_optional_date('', 'test')
        assert result is None

    def test_none(self):
        result = parse_optional_date(None, 'test')
        assert result is None

    def test_whitespace_only(self):
        result = parse_optional_date('   ', 'test')
        assert result is None

    def test_invalid_format(self):
        with pytest.raises(ValueError, match='Format de date invalide'):
            parse_optional_date('15/01/2025', 'test')


class TestAddOneYearSafe:
    def test_normal_date(self):
        d = date(2025, 6, 15)
        result = add_one_year_safe(d)
        assert result == date(2026, 6, 15)

    def test_leap_year_feb_29(self):
        d = date(2024, 2, 29)
        result = add_one_year_safe(d)
        assert result == date(2025, 2, 28)


class TestGetPaymentStatus:
    def test_no_due_date_is_unpaid(self, session):
        ent = Entreprise(nom='T')
        session.add(ent)
        session.commit()
        assert get_payment_status(ent) == 'unpaid'

    def test_paid_is_paid(self, session):
        ent = Entreprise(nom='T', abonnement_paye=True, abonnement_prochaine_echeance=date.today())
        session.add(ent)
        session.commit()
        assert get_payment_status(ent) == 'paid'

    def test_expired(self, session):
        ent = Entreprise(
            nom='T', abonnement_paye=False,
            abonnement_prochaine_echeance=date.today() - timedelta(days=10),
        )
        session.add(ent)
        session.commit()
        assert get_payment_status(ent) == 'expired'

    def test_not_yet_due(self, session):
        ent = Entreprise(
            nom='T', abonnement_paye=False,
            abonnement_prochaine_echeance=date.today() + timedelta(days=10),
        )
        session.add(ent)
        session.commit()
        assert get_payment_status(ent) == 'unpaid'

    def test_custom_today(self, session):
        ent = Entreprise(
            nom='T', abonnement_paye=False,
            abonnement_prochaine_echeance=date(2025, 6, 1),
        )
        session.add(ent)
        session.commit()
        assert get_payment_status(ent, today=date(2025, 5, 15)) == 'unpaid'
        assert get_payment_status(ent, today=date(2025, 6, 2)) == 'expired'


class TestGetEnterpriseQuotaInfo:
    def test_returns_none_for_unknown_plan(self, session):
        ent = Entreprise(nom='T', abonnement_type='nonexistent')
        session.add(ent)
        session.commit()
        result = get_enterprise_quota_info(ent, used_users=1)
        assert result is None

    def test_ok_status(self, session, entreprise):
        result = get_enterprise_quota_info(entreprise, used_users=2)
        assert result is not None
        assert result['status'] == 'ok'
        assert result['plan_label'] == 'Professional'
        assert result['max_users'] == 10
        assert result['used_users'] == 2
        assert result['remaining_users'] == 8

    def test_warning_status(self, session, entreprise):
        result = get_enterprise_quota_info(entreprise, used_users=9)
        assert result['status'] == 'warning'
        assert result['remaining_users'] == 1
        assert result['usage_pct'] == 90

    def test_reached_status(self, session, entreprise):
        result = get_enterprise_quota_info(entreprise, used_users=10)
        assert result['status'] == 'reached'
        assert result['remaining_users'] == 0


class TestApplySubscriptionUpdate:
    def test_invalid_plan_raises(self, session, entreprise):
        with pytest.raises(ValueError, match="Type d'abonnement invalide"):
            apply_subscription_update(entreprise, {'abonnement_type': 'nonexistent'})

    def test_invalid_lifecycle_raises(self, session, entreprise):
        with pytest.raises(ValueError, match='Statut de cycle de vie invalide'):
            apply_subscription_update(entreprise, {'statut': 'bad_status'})

    def test_invalid_montant_raises(self, session, entreprise):
        with pytest.raises(ValueError, match='Montant annuel doit'):
            apply_subscription_update(entreprise, {'montant_annuel_mad': 'abc'})

    def test_invalid_email_raises(self, session, entreprise):
        with pytest.raises(ValueError, match='Email de facturation invalide'):
            apply_subscription_update(entreprise, {'contact_facturation_email': 'not-an-email'})

    def test_invalid_motif_raises(self, session, entreprise):
        with pytest.raises(ValueError, match='Motif de suspension invalide'):
            apply_subscription_update(entreprise, {'motif_suspension': 'bad'})

    def test_valid_update(self, session, entreprise):
        result = apply_subscription_update(entreprise, {
            'abonnement_type': 'premium',
            'statut': 'active',
            'montant_annuel_mad': '15000',
            'contact_facturation_email': 'billing@test.com',
            'motif_suspension': 'demande_client',
            'notes_facturation': 'Some notes',
        })
        assert result.abonnement_type == 'premium'
        assert result.statut == 'active'
        assert result.montant_annuel_mad == 15000
        assert result.contact_facturation_email == 'billing@test.com'
        assert result.motif_suspension == 'demande_client'
        assert result.notes_facturation == 'Some notes'

    def test_mark_unpaid(self, session, entreprise):
        entreprise.abonnement_paye = True
        session.commit()
        apply_subscription_update(entreprise, {'marquer_non_paye': '1'})
        assert entreprise.abonnement_paye is False
        assert entreprise.statut == 'suspended'
        assert entreprise.motif_suspension == 'non_paye'

    def test_clear_motif(self, session, entreprise):
        entreprise.motif_suspension = 'non_paye'
        session.commit()
        apply_subscription_update(entreprise, {'motif_suspension': ''})
        assert entreprise.motif_suspension is None
