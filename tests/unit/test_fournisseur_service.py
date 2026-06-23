"""Tests pour FournisseurService (recalcul du score)."""

import pytest
from app import db
from app.models.partages import Fournisseur
from app.services.fournisseur_service import FournisseurService


@pytest.fixture
def fournisseur(session, entreprise):
    f = Fournisseur(
        entreprise_id=entreprise.id,
        nom='Test Fournisseur',
        domaine='hse',
        statut='actif',
    )
    session.add(f)
    session.commit()
    return f


class TestFournisseurService:
    def test_save_recalculates_score(self, session, fournisseur):
        fournisseur.score_qualite = 4
        fournisseur.score_delai = 3
        fournisseur.score_prix = 5
        result = FournisseurService.save(fournisseur)
        assert result.score_global is not None
        assert result.score_global > 0

    def test_service_inherits_base_crud(self, session, entreprise, fournisseur):
        items = FournisseurService.list(entreprise_id=entreprise.id)
        assert fournisseur in items

        fetched = FournisseurService.get_by_id(fournisseur.id, entreprise.id)
        assert fetched is not None
        assert fetched.id == fournisseur.id

    def test_get_all_by_tenant(self, session, entreprise, fournisseur):
        items = FournisseurService.get_all_by_tenant(entreprise.id)
        assert len(items) >= 1
        assert fournisseur in items
