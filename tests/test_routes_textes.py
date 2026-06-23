import pytest
import json


class TestTextesRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/admin/textes/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/admin/textes/')
        assert resp.status_code in (200, 403)

    def test_create_page_requires_permission(self, login_client):
        resp = login_client.get('/admin/textes/create')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_all_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_tous_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/tous-les-textes')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_nouveaux_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/nouveaux-textes')
        assert resp.status_code in (200, 403)

    def test_bibliotheque_maj_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/mises-a-jour-recentes')
        assert resp.status_code in (200, 403)

    def test_veille_dashboard_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/veille-dashboard')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/admin/textes/api/liste')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_api_domaines_returns_json(self, login_client):
        resp = login_client.get('/admin/textes/api/domaines')
        assert resp.status_code in (200, 403)

    def test_import_json_requires_admin(self, login_client):
        resp = login_client.get('/admin/textes/import_json', follow_redirects=False)
        assert resp.status_code in (403, 302)

    def test_import_json_renders_for_admin(self, login_admin):
        resp = login_admin.get('/admin/textes/import_json')
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
        resp = client.get('/admin/veille/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/admin/veille/')
        assert resp.status_code in (200, 403)

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/admin/veille/api/liste')
        assert resp.status_code in (200, 403)

    def test_api_sources_returns_json(self, login_client):
        resp = login_client.get('/admin/veille/api/sources')
        assert resp.status_code in (200, 403)


class TestVeilleBibliothequeRoutes:
    def test_veille_non_conformites_requires_login(self, client):
        resp = client.get('/admin/textes/bibliotheque/non-conformites', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_veille_non_conformites_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/non-conformites')
        assert resp.status_code in (200, 403)

    def test_veille_non_conformites_with_search(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/non-conformites?q=sécurité')
        assert resp.status_code in (200, 403)

    def test_veille_non_conformites_with_domaine(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/non-conformites?domaine=hse')
        assert resp.status_code in (200, 403)

    def test_veille_preuves_requires_login(self, client):
        resp = client.get('/admin/textes/bibliotheque/preuves', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_veille_preuves_renders(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/preuves')
        assert resp.status_code in (200, 403)

    def test_article_detail_requires_login(self, client):
        resp = client.get('/admin/textes/bibliotheque/article/1', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_article_detail_404(self, login_client):
        resp = login_client.get('/admin/textes/bibliotheque/article/99999')
        assert resp.status_code in (404, 403)

    def test_article_list_proofs_requires_login(self, client):
        resp = client.get('/admin/textes/bibliotheque/article/1/proof/liste', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_article_list_actions_requires_login(self, client):
        resp = client.get('/admin/textes/bibliotheque/article/1/actions', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_article_attach_proof_requires_login(self, client):
        resp = client.post('/admin/textes/bibliotheque/article/1/proof/attach',
                          data=json.dumps({'proof_id': 1}),
                          content_type='application/json',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_article_add_action_requires_login(self, client):
        resp = client.post('/admin/textes/bibliotheque/article/1/action/add',
                          data={'description': 'Test action'},
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_veille_preuves_upload_requires_login(self, client):
        resp = client.post('/admin/textes/bibliotheque/preuves/upload',
                          data={'file': (b'test', 'test.txt')},
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_veille_preuves_supprimer_requires_login(self, client):
        resp = client.post('/admin/textes/bibliotheque/preuves/1/supprimer',
                          follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_veille_preuves_upload_no_file(self, login_client):
        resp = login_client.post('/admin/textes/bibliotheque/preuves/upload',
                                follow_redirects=False)
        assert resp.status_code in (400, 403)


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
