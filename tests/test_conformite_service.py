import pytest
from datetime import date, datetime, timedelta
from app import db
from app.models import (
    EvaluationArticle, ApplicabiliteEnum, ConformiteEnum,
)
from app.services.conformite_service import (
    normalize_core_dict,
    build_evaluation_stats,
    build_proof_state_for_documents,
    add_years_safe,
    parse_optional_date,
)
from types import SimpleNamespace


class TestNormalizeCoreDict:
    def test_all_none(self):
        result = normalize_core_dict({})
        assert result == {'applicable': '', 'conforme': '', 'observation': '', 'date_evaluation': ''}

    def test_with_values(self):
        result = normalize_core_dict({
            'applicable': ' Applicable ',
            'conforme': 'Conforme',
            'observation': 'All good',
        })
        assert result['applicable'] == 'Applicable'
        assert result['conforme'] == 'Conforme'
        assert result['observation'] == 'All good'

    def test_non_string_values(self):
        result = normalize_core_dict({'applicable': 123, 'conforme': None})
        assert result['applicable'] == '123'
        assert result['conforme'] == ''


class TestBuildEvaluationStats:
    def test_empty_articles(self):
        stats = build_evaluation_stats([])
        assert stats['total'] == 0
        assert stats['score_conformite'] == 0

    def test_mixed_evaluations(self):
        articles = [
            SimpleNamespace(applicable=ApplicabiliteEnum.APPLICABLE, conforme=ConformiteEnum.CONFORME),
            SimpleNamespace(applicable=ApplicabiliteEnum.APPLICABLE, conforme=ConformiteEnum.NON_CONFORME),
            SimpleNamespace(applicable=ApplicabiliteEnum.NON_APPLICABLE, conforme=None),
            SimpleNamespace(applicable=ApplicabiliteEnum.A_CONFIRMER, conforme=None),
            SimpleNamespace(applicable=None, conforme=None),
        ]
        stats = build_evaluation_stats(articles)
        assert stats['total'] == 5
        assert stats['evaluees'] == 4
        assert stats['applicables'] == 3
        assert stats['conformes'] == 1
        assert stats['non_conformes'] == 1
        assert stats['non_applicables'] == 1
        assert stats['a_confirmer'] == 1
        assert stats['score_conformite'] == pytest.approx(33.33, abs=0.1)

    def test_all_applicable_none(self):
        articles = [
            SimpleNamespace(applicable=ApplicabiliteEnum.APPLICABLE, conforme=ConformiteEnum.CONFORME),
            SimpleNamespace(applicable=ApplicabiliteEnum.APPLICABLE, conforme=ConformiteEnum.CONFORME),
        ]
        stats = build_evaluation_stats(articles)
        assert stats['score_conformite'] == 100.0

    def test_no_applicables(self):
        articles = [
            SimpleNamespace(applicable=ApplicabiliteEnum.NON_APPLICABLE, conforme=None),
        ]
        stats = build_evaluation_stats(articles)
        assert stats['score_conformite'] == 0


class TestBuildProofStateForDocuments:
    def test_no_documents(self):
        state = build_proof_state_for_documents([])
        assert state['state'] == 'missing'
        assert state['expires_at'] is None

    def test_no_validity_dates(self):
        docs = [SimpleNamespace(validite=None)]
        state = build_proof_state_for_documents(docs)
        assert state['state'] == 'valid'
        assert state['expires_at'] is None

    def test_valid_document(self):
        docs = [SimpleNamespace(validite=date(2026, 1, 1))]
        state = build_proof_state_for_documents(docs, reference_date=date(2025, 6, 1))
        assert state['state'] == 'valid'
        assert state['expires_at'] == date(2026, 1, 1)

    def test_expiring_soon(self):
        docs = [SimpleNamespace(validite=date(2025, 6, 20))]
        state = build_proof_state_for_documents(docs, reference_date=date(2025, 6, 1))
        assert state['state'] == 'expiring_soon'

    def test_expired(self):
        docs = [SimpleNamespace(validite=date(2025, 1, 1))]
        state = build_proof_state_for_documents(docs, reference_date=date(2025, 6, 1))
        assert state['state'] == 'expired'

    def test_earliest_date_wins(self):
        docs = [
            SimpleNamespace(validite=date(2026, 6, 1)),
            SimpleNamespace(validite=date(2025, 3, 1)),
        ]
        state = build_proof_state_for_documents(docs, reference_date=date(2025, 6, 1))
        assert state['state'] == 'expired'
        assert state['expires_at'] == date(2025, 3, 1)


class TestAddYearsSafe:
    def test_normal(self):
        assert add_years_safe(date(2025, 6, 15), 1) == date(2026, 6, 15)

    def test_leap_year(self):
        assert add_years_safe(date(2024, 2, 29), 1) == date(2025, 2, 28)

    def test_multiple_years(self):
        assert add_years_safe(date(2020, 3, 10), 5) == date(2025, 3, 10)


class TestParseOptionalDateConformite:
    def test_valid(self):
        assert parse_optional_date('2025-06-15') == date(2025, 6, 15)

    def test_empty(self):
        assert parse_optional_date('') is None

    def test_none(self):
        assert parse_optional_date(None) is None

    def test_invalid(self):
        with pytest.raises(ValueError):
            parse_optional_date('invalid')
