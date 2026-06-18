import pytest
from app import db


class TestLoginRoute:
    def test_login_page_renders(self, client):
        resp = client.get('/users/login')
        assert resp.status_code == 200

    def test_login_with_valid_credentials(self, client, manager_user):
        resp = client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_with_invalid_credentials(self, client, manager_user):
        resp = client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'wrongpassword',
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestDashboardRoute:
    def test_dashboard_requires_login(self, client):
        resp = client.get('/tableau-de-bord', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_dashboard_renders_for_authenticated_user(self, login_client):
        resp = login_client.get('/tableau-de-bord')
        assert resp.status_code == 200


class TestActionsRoutes:
    def test_list_actions_requires_login(self, client):
        resp = client.get('/actions/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_actions_renders(self, login_client):
        resp = login_client.get('/actions/')
        assert resp.status_code == 200

    def test_create_action_page_renders(self, login_client):
        resp = login_client.get('/actions/nouveau')
        assert resp.status_code in (200, 302, 403, 404)


class TestDocumentsRoutes:
    def test_list_documents_requires_login(self, client):
        resp = client.get('/documents/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_documents_renders(self, login_client):
        resp = login_client.get('/documents/')
        assert resp.status_code == 200


class TestAdminRoutes:
    def test_admin_requires_system_role(self, login_client):
        resp = login_client.get('/admin/', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_admin_dashboard_renders(self, login_admin):
        resp = login_admin.get('/admin/')
        assert resp.status_code == 200


class TestSupportRoutes:
    def test_list_tickets_renders(self, login_client):
        resp = login_client.get('/support/')
        assert resp.status_code == 200


class TestTextesRoutes:
    def test_list_textes_renders(self, login_client):
        resp = login_client.get('/textes/')
        assert resp.status_code == 200


class TestAuditRoutes:
    def test_list_audits_renders(self, login_client):
        resp = login_client.get('/audit/')
        assert resp.status_code == 200


class TestIndicateursRoutes:
    def test_list_indicateurs_renders(self, login_client):
        resp = login_client.get('/indicateurs/')
        assert resp.status_code == 200


class TestQualiteRoutes:
    def test_qualite_dashboard_renders(self, login_client):
        resp = login_client.get('/qualite/')
        assert resp.status_code in (200, 403)


class TestAPIStats:
    def test_api_stats_requires_login(self, client):
        resp = client.get('/api/stats', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/api/stats')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'
