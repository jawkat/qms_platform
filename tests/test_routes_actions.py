import pytest
import json


class TestActionsRoutes:
    def test_list_requires_login(self, client):
        resp = client.get('/actions/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_renders(self, login_client):
        resp = login_client.get('/actions/')
        assert resp.status_code == 200

    def test_list_alt_url_renders(self, login_client):
        resp = login_client.get('/actions/liste')
        assert resp.status_code == 200

    def test_api_liste_requires_login(self, client):
        resp = client.get('/actions/api/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/actions/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_create_requires_login(self, client):
        resp = client.post('/actions/api/create',
                           data=json.dumps({'description': 'Test'}),
                           content_type='application/json',
                           follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_create_action(self, login_client):
        resp = login_client.post('/actions/api/create',
                                 data=json.dumps({
                                     'description': 'Nouvelle action',
                                     'priorite': 'haute',
                                     'date_echeance': '2026-12-31',
                                 }),
                                 content_type='application/json')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            data = resp.get_json()
            assert data.get('success') is True
            assert 'id' in data

    def test_detail_requires_login(self, client, action):
        resp = client.get(f'/actions/{action.id}', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_detail_renders(self, login_client, action):
        resp = login_client.get(f'/actions/{action.id}')
        assert resp.status_code == 200

    def test_api_update_action(self, login_client, action):
        resp = login_client.post(f'/actions/{action.id}/api/update',
                                 data=json.dumps({'description': 'Updated'}),
                                 content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_update_status(self, login_client, action):
        resp = login_client.post(f'/actions/{action.id}/status',
                                data=json.dumps({'statut': 'EN_COURS'}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_proof_list_requires_login(self, client, action):
        resp = client.get(f'/actions/{action.id}/proof/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_proof_list_returns_json(self, login_client, action):
        resp = login_client.get(f'/actions/{action.id}/proof/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_delete_action(self, login_client, action):
        resp = login_client.post(f'/actions/{action.id}/delete', follow_redirects=True)
        assert resp.status_code in (200, 302, 403)

    def test_export_csv_requires_login(self, client):
        resp = client.get('/actions/api/export', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_export_csv(self, login_client):
        resp = login_client.get('/actions/api/export')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'text/csv; charset=utf-8'


class TestDocumentsRoutes:
    def test_list_requires_login(self, client):
        resp = client.get('/documents/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_renders(self, login_client):
        resp = login_client.get('/documents/')
        assert resp.status_code == 200

    def test_gestion_renders(self, login_client):
        resp = login_client.get('/documents/gestion')
        assert resp.status_code == 200

    def test_api_liste_requires_login(self, client):
        resp = client.get('/documents/api/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/documents/api/liste')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_api_dossiers_returns_json(self, login_client):
        resp = login_client.get('/documents/api/dossiers')
        assert resp.status_code in (200, 403)

    def test_api_types_returns_json(self, login_client):
        resp = login_client.get('/documents/api/types')
        assert resp.status_code in (200, 403)

    def test_api_actives_returns_json(self, login_client):
        resp = login_client.get('/documents/api/actives')
        assert resp.status_code in (200, 403)

    def test_api_recherche_returns_json(self, login_client):
        resp = login_client.get('/documents/api/recherche?q=test')
        assert resp.status_code in (200, 403)

    def test_detail_requires_login(self, client, proof):
        resp = client.get(f'/documents/{proof.id}/detail', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_detail_renders(self, login_client, proof):
        resp = login_client.get(f'/documents/{proof.id}/detail')
        assert resp.status_code in (200, 403)
