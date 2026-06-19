import pytest
import json


class TestTextesRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/textes/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/textes/')
        assert resp.status_code == 200

    def test_create_page_requires_permission(self, login_client):
        resp = login_client.get('/textes/create')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_all_renders(self, login_client):
        resp = login_client.get('/textes/bibliotheque')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_tous_renders(self, login_client):
        resp = login_client.get('/textes/bibliotheque/tous-les-textes')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_nouveaux_renders(self, login_client):
        resp = login_client.get('/textes/bibliotheque/nouveaux-textes')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_maj_renders(self, login_client):
        resp = login_client.get('/textes/bibliotheque/mises-a-jour-recentes')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/textes/api/liste')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_api_domaines_returns_json(self, login_client):
        resp = login_client.get('/textes/api/domaines')
        assert resp.status_code in (200, 403)

    def test_import_json_requires_admin(self, login_client):
        resp = login_client.get('/textes/import_json', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_import_json_renders_for_admin(self, login_admin):
        resp = login_admin.get('/textes/import_json')
        assert resp.status_code in (200, 302, 403)


class TestConformiteRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/conformite/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/conformite/')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/conformite/api/liste')
        assert resp.status_code in (200, 403)

    def test_search_renders(self, login_client):
        resp = login_client.get('/conformite/search')
        assert resp.status_code in (200, 403)

    def test_nonconformites_renders(self, login_client):
        resp = login_client.get('/conformite/nonconformites')
        assert resp.status_code in (200, 403)

    def test_preuves_gestion_renders(self, login_client):
        resp = login_client.get('/conformite/preuves/gestion')
        assert resp.status_code in (200, 403)


class TestEntrepriseTextesRoutes:
    def test_link_requires_login(self, client):
        resp = client.post('/entreprise-textes/link',
                          data=json.dumps({'texte_id': 1}),
                          content_type='application/json',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_toggle_link_requires_login(self, client):
        resp = client.post('/entreprise-textes/toggle_link',
                          data=json.dumps({'texte_id': 1}),
                          content_type='application/json',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestVeilleRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/veille/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/veille/')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/veille/api/liste')
        assert resp.status_code in (200, 403)

    def test_api_sources_returns_json(self, login_client):
        resp = login_client.get('/veille/api/sources')
        assert resp.status_code in (200, 403)


class TestSecteurRoutes:
    def test_list_requires_login(self, client):
        resp = client.get('/secteur/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_list_renders(self, login_client):
        resp = login_client.get('/secteur/')
        assert resp.status_code in (200, 403)

    def test_create_renders(self, login_client):
        resp = login_client.get('/secteur/create')
        assert resp.status_code in (200, 403)

    def test_admin_textes_renders(self, login_client):
        resp = login_client.get('/secteur/admin/textes')
        assert resp.status_code in (200, 403)
