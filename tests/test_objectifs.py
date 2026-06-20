import pytest
from app import db
from app.models.qualite import ObjectifQualite
from datetime import date


@pytest.fixture
def objectif(session, entreprise, manager_user, indicateur):
    obj = ObjectifQualite(
        entreprise_id=entreprise.id,
        titre='Réduire les NC de 50%',
        description='Objectif qualité annuel',
        indicateur_id=indicateur.id,
        cible=90.0,
        seuil_alerte=70.0,
        pilote_id=manager_user.id,
        date_debut=date(2026, 1, 1),
        date_echeance=date(2026, 12, 31),
        statut='en_cours',
        domaine='qualite',
        processus_concerne='Production',
    )
    session.add(obj)
    session.commit()
    return obj


class TestObjectifsPages:
    def test_index_renders(self, login_client):
        resp = login_client.get('/objectifs/')
        assert resp.status_code == 200

    def test_requires_login(self, client):
        resp = client.get('/objectifs/', follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestObjectifsAPI:
    def test_liste_vide(self, login_client):
        resp = login_client.get('/objectifs/api/liste')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_creer_objectif(self, login_client, indicateur, manager_user):
        resp = login_client.post('/objectifs/api/creer', json={
            'titre': 'Améliorer la qualité',
            'description': 'Test',
            'indicateur_id': indicateur.id,
            'cible': 95.0,
            'seuil_alerte': 75.0,
            'pilote_id': manager_user.id,
            'date_debut': '2026-01-01',
            'date_echeance': '2026-12-31',
            'statut': 'en_cours',
            'domaine': 'qualite',
            'processus_concerne': 'Production',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'id' in data

    def test_liste_apres_creation(self, login_client, objectif):
        resp = login_client.get('/objectifs/api/liste')
        items = resp.get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Réduire les NC de 50%'

    def test_update_objectif(self, login_client, objectif):
        resp = login_client.post(f'/objectifs/api/{objectif.id}/modifier', json={
            'statut': 'atteint',
            'cible': 100.0,
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_delete_objectif(self, login_client, objectif):
        resp = login_client.post(f'/objectifs/api/{objectif.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_delete_introuvable(self, login_client):
        resp = login_client.post('/objectifs/api/99999/supprimer', json={})
        assert resp.status_code == 404

    def test_stats(self, login_client, objectif):
        resp = login_client.get('/objectifs/api/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1
        assert data['en_cours'] >= 1
        assert 'atteint' in data
        assert 'en_retard' in data
        assert 'non_atteint' in data
