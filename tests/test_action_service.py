import pytest
from datetime import date, timedelta
from app import db
from app.models import ActionCorrective, Utilisateur
from app.services.action_service import ActionService


class TestActionServiceGenerateNextOccurrence:
    def test_not_recurrent_returns_none(self, session, action):
        result = ActionService.generate_next_occurrence(action)
        assert result is None

    def test_no_frequency_returns_none(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='No freq',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            est_recurrente=True,
            frequence=None,
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is None

    def test_unknown_frequency_returns_none(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Unknown freq',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            est_recurrente=True,
            frequence='unknown',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is None

    def test_weekly_frequency(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Weekly',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 1, 6),
            est_recurrente=True,
            frequence='hebdomadaire',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2025, 1, 13)
        assert result.statut == 'A_FAIRE'
        assert result.est_recurrente is True
        assert result.parent_action_id == action.id

    def test_monthly_frequency(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Monthly',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 1, 15),
            est_recurrente=True,
            frequence='mensuel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2025, 2, 15)

    def test_monthly_frequency_end_of_month(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Monthly EOM',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 1, 31),
            est_recurrente=True,
            frequence='mensuel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2025, 2, 28)

    def test_quarterly_frequency(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Quarterly',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 1, 15),
            est_recurrente=True,
            frequence='trimestriel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2025, 4, 15)

    def test_quarterly_frequency_year_cross(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Quarterly year cross',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 11, 15),
            est_recurrente=True,
            frequence='trimestriel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2026, 2, 15)

    def test_annual_frequency(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Annual',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 6, 15),
            est_recurrente=True,
            frequence='annuel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2026, 6, 15)

    def test_annual_leap_year(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Leap year',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2024, 2, 29),
            est_recurrente=True,
            frequence='annuel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result is not None
        assert result.date_echeance == date(2025, 2, 28)

    def test_new_action_copies_properties(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Copy test',
            type_action='preventive',
            priorite='critique',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date(2025, 3, 10),
            est_recurrente=True,
            frequence='mensuel',
        )
        session.add(action)
        session.commit()
        result = ActionService.generate_next_occurrence(action)
        assert result.description == 'Copy test'
        assert result.type_action == 'preventive'
        assert result.priorite == 'critique'
        assert result.responsable_id == manager_user.id
        assert result.entreprise_id == entreprise.id
