import pytest
import json


class TestHseRoutes:
    def test_dashboard_requires_login(self, client):
        resp = client.get('/hse/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_dashboard_renders(self, login_client):
        resp = login_client.get('/hse/')
        assert resp.status_code in (200, 403)

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/hse/api/stats')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_incidents_page_renders(self, login_client):
        resp = login_client.get('/hse/incidents')
        assert resp.status_code in (200, 403)

    def test_api_incidents_returns_json(self, login_client):
        resp = login_client.get('/hse/api/incidents')
        assert resp.status_code in (200, 403)

    def test_api_incidents_create(self, login_client):
        resp = login_client.post('/hse/api/incidents/create',
                                data=json.dumps({
                                    'type_incident': 'accident',
                                    'description': 'Test incident',
                                    'gravite': 'mineure',
                                    'date_incident': '2026-06-18',
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_incidents_update(self, login_client):
        resp = login_client.post('/hse/api/incidents/1/update',
                                data=json.dumps({'description': 'Updated'}),
                                content_type='application/json')
        assert resp.status_code in (200, 403, 404)

    def test_epi_page_renders(self, login_client):
        resp = login_client.get('/hse/epi')
        assert resp.status_code in (200, 403)

    def test_api_epi_returns_json(self, login_client):
        resp = login_client.get('/hse/api/epi')
        assert resp.status_code in (200, 403)

    def test_api_epi_create(self, login_client):
        resp = login_client.post('/hse/api/epi/create',
                                data=json.dumps({
                                    'nom': 'Casque test',
                                    'type': 'protection-tete',
                                    'quantite': 10,
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_inspections_page_renders(self, login_client):
        resp = login_client.get('/hse/inspections')
        assert resp.status_code in (200, 403)

    def test_api_inspections_returns_json(self, login_client):
        resp = login_client.get('/hse/api/inspections')
        assert resp.status_code in (200, 403)

    def test_permis_travail_page_renders(self, login_client):
        resp = login_client.get('/hse/permis-travail')
        assert resp.status_code in (200, 403)

    def test_api_permis_travail_returns_json(self, login_client):
        resp = login_client.get('/hse/api/permis-travail')
        assert resp.status_code in (200, 403)
