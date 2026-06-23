import pytest
import json


class TestAuditRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/audit/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/audit/')
        assert resp.status_code == 200

    def test_api_liste_requires_login(self, client):
        resp = client.get('/audit/api/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/audit/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_creer_requires_login(self, client):
        resp = client.post('/audit/creer',
                          data=json.dumps({'type': 'interne'}),
                          content_type='application/json',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_creer_audit(self, login_client):
        resp = login_client.post('/audit/creer',
                                data=json.dumps({
                                    'type': 'interne',
                                    'date_audit': '2026-12-31',
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 201, 403)

    def test_detail_requires_login(self, client, audit_record):
        resp = client.get(f'/audit/{audit_record.id}', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_detail_renders(self, login_client, audit_record):
        resp = login_client.get(f'/audit/{audit_record.id}')
        assert resp.status_code == 200

    def test_update_audit(self, login_client, audit_record):
        resp = login_client.post(f'/audit/{audit_record.id}/update',
                                data=json.dumps({'commentaire': 'Updated'}),
                                content_type='application/json')
        assert resp.status_code in (200, 201, 403)

    def test_export_csv(self, login_client):
        resp = login_client.get('/audit/api/export')
        assert resp.status_code in (200, 201, 403)
        if resp.status_code == 200:
            assert 'csv' in resp.content_type or 'text' in resp.content_type


class TestIndicateursRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/indicateurs/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/indicateurs/')
        assert resp.status_code == 200

    def test_api_liste_requires_login(self, client):
        resp = client.get('/indicateurs/api/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/indicateurs/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_create_requires_login(self, client):
        resp = client.post('/indicateurs/api/create',
                          data=json.dumps({'nom': 'Test', 'periode': 'mensuel'}),
                          content_type='application/json',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_create_indicateur(self, login_client):
        resp = login_client.post('/indicateurs/api/create',
                                data=json.dumps({
                                    'nom': 'Test indicateur',
                                    'description': 'Description',
                                    'periode': 'mensuel',
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 201, 403)

    def test_detail_requires_login(self, client, indicateur):
        resp = client.get(f'/indicateurs/{indicateur.id}', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_detail_renders(self, login_client, indicateur):
        resp = login_client.get(f'/indicateurs/{indicateur.id}')
        assert resp.status_code in (200, 201, 403)
