"""Tests unitaires pour BaseService (couche métier pure)."""

import pytest
from app import db
from app.models import ActionCorrective
from app.services.base import BaseService

# Concrete service for testing (BaseService has model=None)
class _TestService(BaseService):
    model = ActionCorrective


class TestBaseServiceGetById:
    def test_returns_none_when_not_found(self, session):
        result = _TestService.get_by_id(item_id=9999)
        assert result is None

    def test_returns_item_when_found(self, session, action):
        result = _TestService.get_by_id(item_id=action.id)
        assert result is not None
        assert result.id == action.id

    def test_scoped_by_entreprise(self, session, action, entreprise):
        result = _TestService.get_by_id(item_id=action.id, entreprise_id=9999)
        assert result is None


class TestBaseServiceList:
    def test_list_all(self, session, action):
        items = _TestService.list()
        assert len(items) >= 1
        assert action in items

    def test_list_filtered(self, session, action):
        items = _TestService.list(filters={'statut': 'A_FAIRE'})
        assert action in items

        items = _TestService.list(filters={'statut': 'FAIT'})
        assert action not in items

    def test_list_search(self, session, action):
        items = _TestService.list(search='corrective', search_fields=['description'])
        assert action in items

        items = _TestService.list(search='nonexistent', search_fields=['description'])
        assert action not in items

    def test_list_tenant_scoped(self, session, action, entreprise):
        items = _TestService.list(entreprise_id=entreprise.id)
        assert action in items

        items = _TestService.list(entreprise_id=9999)
        assert action not in items

    def test_list_sorted(self, session, action, manager_user):
        a2 = ActionCorrective(
            entreprise_id=action.entreprise_id,
            description='Older action',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
        )
        session.add(a2)
        session.commit()

        items = _TestService.list(sort_field='date_creation', sort_dir='asc')
        assert items[0].id == min(action.id, a2.id)

        items = _TestService.list(sort_field='date_creation', sort_dir='desc')
        assert items[0].id == max(action.id, a2.id)


class TestBaseServiceSave:
    def test_save_creates_new_record(self, session, entreprise):
        from app.models.haccp import ProcessusHaccp
        p = ProcessusHaccp(entreprise_id=entreprise.id, etape='Test', description='Test')
        result = _TestService.save(p)
        assert result.id is not None
        assert ProcessusHaccp.query.count() >= 1

    def test_save_updates_existing(self, session, action):
        action.description = 'Modified'
        result = _TestService.save(action)
        assert result.description == 'Modified'
        fetched = ActionCorrective.query.get(action.id)
        assert fetched.description == 'Modified'


class TestBaseServiceRemove:
    def test_remove_deletes_record(self, session, action):
        _TestService.remove(action)
        assert ActionCorrective.query.get(action.id) is None
