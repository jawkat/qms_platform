"""Tests pour PrpService / OprpService (filtrage par type_prp)."""

import pytest
from app import db
from app.models.haccp import Prp
from app.services.haccp_service import PrpService, OprpService


def _make_prp(db_session, ent, **kw):
    defaults = dict(categorie='hygiene', element='Nettoyage')
    defaults.update(kw)
    p = Prp(entreprise_id=ent.id, **defaults)
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture
def generic_prp(session, entreprise):
    return _make_prp(session, entreprise, type_prp='generic', description='PRP generic')


@pytest.fixture
def operational_prp(session, entreprise):
    return _make_prp(session, entreprise, type_prp='operational', description='PRP operational')


class TestPrpService:
    def test_list_only_returns_generic(self, session, generic_prp, operational_prp):
        items = PrpService.list()
        ids = [i.id for i in items]
        assert generic_prp.id in ids
        assert operational_prp.id not in ids

    def test_get_by_id_returns_generic(self, session, generic_prp, operational_prp):
        assert PrpService.get_by_id(generic_prp.id) is not None
        # OprpService cannot access generic PRP
        assert PrpService.get_by_id(operational_prp.id) is None

    def test_save_sets_type_prp(self, session, entreprise):
        p = Prp(entreprise_id=entreprise.id, categorie='hygiene', element='Nettoyage', description='New generic')
        result = PrpService.save(p)
        assert result.type_prp == 'generic'

    def test_get_all_by_tenant_is_filtered(self, session, generic_prp, operational_prp, entreprise):
        items = PrpService.get_all_by_tenant(entreprise.id)
        assert len(items) == 1
        assert items[0].id == generic_prp.id


class TestOprpService:
    def test_list_only_returns_operational(self, session, generic_prp, operational_prp):
        items = OprpService.list()
        ids = [i.id for i in items]
        assert operational_prp.id in ids
        assert generic_prp.id not in ids

    def test_get_by_id_returns_operational(self, session, generic_prp, operational_prp):
        assert OprpService.get_by_id(operational_prp.id) is not None
        assert OprpService.get_by_id(generic_prp.id) is None

    def test_save_sets_type_prp(self, session, entreprise):
        p = Prp(entreprise_id=entreprise.id, categorie='hygiene', element='Nettoyage', description='New operational')
        result = OprpService.save(p)
        assert result.type_prp == 'operational'
