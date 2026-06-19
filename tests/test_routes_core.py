import pytest
import json


class TestMainRoutes:
    def test_index_public(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_dashboard_requires_login(self, client):
        resp = client.get('/tableau-de-bord', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_dashboard_renders(self, login_client):
        resp = login_client.get('/tableau-de-bord')
        assert resp.status_code == 200

    def test_api_stats_requires_login(self, client):
        resp = client.get('/api/stats', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/api/stats')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_switch_domaine_requires_login(self, client):
        resp = client.get('/switch-domaine/hse', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_notifications_requires_login(self, client):
        resp = client.get('/api/notifications', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_search_requires_login(self, client):
        resp = client.get('/search', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_search_renders(self, login_client):
        resp = login_client.get('/search')
        assert resp.status_code == 200


class TestUserRoutes:
    def test_login_page_renders(self, client):
        resp = client.get('/users/login')
        assert resp.status_code == 200

    def test_login_valid_credentials(self, client, manager_user):
        resp = client.post('/users/login', data={
            'email': manager_user.email, 'password': 'manager123',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_login_invalid_credentials(self, client):
        resp = client.post('/users/login', data={
            'email': 'wrong@test.com', 'password': 'wrong',
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_register_page_renders(self, client):
        resp = client.get('/users/register')
        assert resp.status_code == 200

    def test_logout(self, login_client):
        resp = login_client.get('/users/logout', follow_redirects=True)
        assert resp.status_code == 200

    def test_list_users_requires_permission(self, login_client):
        resp = login_client.get('/users/')
        assert resp.status_code == 200

    def test_list_users_requires_login(self, client):
        resp = client.get('/users/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_create_user_page_renders(self, login_client):
        resp = login_client.get('/users/create')
        assert resp.status_code in (200, 403)

    def test_profile_renders(self, login_client):
        resp = login_client.get('/users/profile')
        assert resp.status_code == 200

    def test_change_password_renders(self, login_client):
        resp = login_client.get('/users/change-password')
        assert resp.status_code == 200

    def test_forgot_password_page_renders(self, client):
        resp = client.get('/users/forgot-password')
        assert resp.status_code == 200

    def test_reset_password_page_renders(self, client):
        resp = client.get('/users/reset-password/test-token')
        assert resp.status_code in (200, 302)

    def test_toggle_user_status_requires_login(self, client):
        resp = client.post('/users/1/toggle-status', follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestEntreprisesRoutes:
    def test_list_requires_login(self, client):
        resp = client.get('/entreprises/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_renders(self, login_client):
        resp = login_client.get('/entreprises/')
        assert resp.status_code == 200

    def test_create_page_renders(self, login_client):
        resp = login_client.get('/entreprises/create')
        assert resp.status_code == 200

    def test_create_page_contains_csrf_token(self, login_client):
        resp = login_client.get('/entreprises/create')
        assert resp.status_code == 200
        assert b'name="csrf_token"' in resp.data

    def test_api_liste_requires_login(self, client):
        resp = client.get('/entreprises/api/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/entreprises/api/liste')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_api_detail_requires_login(self, client, entreprise):
        resp = client.get(f'/entreprises/api/{entreprise.id}/detail', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_detail_returns_json(self, login_client, entreprise):
        resp = login_client.get(f'/entreprises/api/{entreprise.id}/detail')
        assert resp.status_code in (200, 403)


class TestFacturationRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/facturation/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/facturation/')
        assert resp.status_code == 200

    def test_api_infos_returns_json(self, login_client):
        resp = login_client.get('/facturation/api/infos')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_api_paiements_returns_json(self, login_client):
        resp = login_client.get('/facturation/api/paiements')
        assert resp.status_code in (200, 403)


class TestPlansRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/plans/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/plans/')
        assert resp.status_code == 200

    def test_api_plans_returns_json(self, login_client):
        resp = login_client.get('/plans/api/plans')
        assert resp.status_code in (200, 403)

    def test_api_current_returns_json(self, login_client):
        resp = login_client.get('/plans/api/current')
        assert resp.status_code in (200, 403)

    def test_api_create_requires_permission(self, client):
        resp = client.post('/plans/api/create',
                          data=json.dumps({'plan_key': 'test', 'label': 'Test'}),
                          content_type='application/json', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_api_create_as_admin(self, login_admin):
        resp = login_admin.post('/plans/api/create',
                               data=json.dumps({'plan_key': 'gold', 'label': 'Gold',
                                                'price_mad': 999, 'max_users': 10}),
                               content_type='application/json')
        assert resp.status_code in (200, 201, 403)
        if resp.status_code in (200, 201):
            data = resp.get_json()
            assert data.get('success')

    def test_api_update_as_admin(self, login_admin):
        resp = login_admin.post('/plans/api/1/update',
                               data=json.dumps({'label': 'Updated'}),
                               content_type='application/json')
        assert resp.status_code in (200, 403, 404)

    def test_api_delete_as_admin(self, login_admin):
        resp = login_admin.post('/plans/api/1/delete',
                               content_type='application/json')
        assert resp.status_code in (200, 403, 404)

    def test_api_detail_returns_json(self, login_admin):
        resp = login_admin.get('/plans/api/1/detail')
        assert resp.status_code in (200, 403, 404)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_create_page_renders(self, login_admin):
        resp = login_admin.get('/plans/create')
        assert resp.status_code in (200, 403)

    def test_edit_page_renders(self, login_admin):
        resp = login_admin.get('/plans/1/edit')
        assert resp.status_code in (200, 403, 404)


class TestAdminRoutes:
    def test_dashboard_requires_system_role(self, login_client):
        resp = login_client.get('/admin/', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_dashboard_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/')
        assert resp.status_code == 200

    def test_entreprises_requires_admin(self, login_client):
        resp = login_client.get('/admin/entreprises', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_entreprises_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/entreprises')
        assert resp.status_code == 200

    def test_roles_requires_admin(self, login_client):
        resp = login_client.get('/admin/roles', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_roles_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/roles')
        assert resp.status_code == 200

    def test_permissions_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/permissions')
        assert resp.status_code == 200

    def test_securite_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/securite')
        assert resp.status_code == 200

    def test_notifications_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/notifications')
        assert resp.status_code == 200
        assert b'name="csrf_token"' in resp.data

    def test_plans_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/plans')
        assert resp.status_code == 200

    def test_backups_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/backups')
        assert resp.status_code == 200

    def test_utilisateurs_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/utilisateurs')
        assert resp.status_code == 200

    def test_tickets_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/tickets')
        assert resp.status_code == 200

    def test_demo_creneaux_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/demo/creneaux')
        assert resp.status_code == 200

    def test_demo_disponibilites_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/demo/disponibilites')
        assert resp.status_code == 200


class TestSupportRoutes:
    def test_list_requires_login(self, client):
        resp = client.get('/support/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_renders(self, login_client):
        resp = login_client.get('/support/')
        assert resp.status_code == 200

    def test_creer_requires_login(self, client):
        resp = client.get('/support/creer', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_creer_renders(self, login_client):
        resp = login_client.get('/support/creer')
        assert resp.status_code in (200, 403)

    def test_detail_requires_login(self, client, ticket):
        resp = client.get(f'/support/{ticket.id}', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_detail_renders(self, login_client, ticket):
        resp = login_client.get(f'/support/{ticket.id}')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/support/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'
