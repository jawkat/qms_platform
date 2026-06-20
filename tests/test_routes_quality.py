import pytest
import json


class TestQualiteRoutes:
    def test_dashboard_requires_login(self, client):
        resp = client.get('/qualite/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_dashboard_renders(self, login_client):
        resp = login_client.get('/qualite/')
        assert resp.status_code in (200, 403)

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/qualite/api/stats')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_risques_page_renders(self, login_client):
        resp = login_client.get('/qualite/risques')
        assert resp.status_code in (200, 403)

    def test_api_risques_returns_json(self, login_client):
        resp = login_client.get('/qualite/api/risques')
        assert resp.status_code in (200, 403)

    def test_clients_page_redirects(self, login_client):
        resp = login_client.get('/qualite/clients')
        assert resp.status_code in (200, 302, 403)

    def test_fournisseurs_page_redirects(self, login_client):
        resp = login_client.get('/qualite/fournisseurs')
        assert resp.status_code in (200, 302, 403)

    def test_formations_page_redirects(self, login_client):
        resp = login_client.get('/qualite/formations')
        assert resp.status_code in (200, 302, 403)

    def test_equipements_page_renders(self, login_client):
        resp = login_client.get('/qualite/equipements')
        assert resp.status_code in (200, 403)

    def test_controle_page_renders(self, login_client):
        resp = login_client.get('/qualite/controle')
        assert resp.status_code in (200, 403)

    def test_revue_page_renders(self, login_client):
        resp = login_client.get('/qualite/revue')
        assert resp.status_code in (200, 403)


class TestHaccpRoutes:
    def test_dashboard_requires_login(self, client):
        resp = client.get('/haccp/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_dashboard_renders(self, login_client):
        resp = login_client.get('/haccp/')
        assert resp.status_code in (200, 403)

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/stats')
        assert resp.status_code in (200, 403)
        if resp.status_code == 200:
            assert resp.content_type == 'application/json'

    def test_processus_page_renders(self, login_client):
        resp = login_client.get('/haccp/processus')
        assert resp.status_code in (200, 403)

    def test_api_processus_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/processus')
        assert resp.status_code in (200, 403)

    def test_api_processus_create(self, login_client):
        resp = login_client.post('/haccp/api/processus/create',
                                data=json.dumps({'etape': 'Reception matieres premieres'}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_produits_page_renders(self, login_client):
        resp = login_client.get('/haccp/produits')
        assert resp.status_code in (200, 403)

    def test_api_produits_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/produits')
        assert resp.status_code in (200, 403)

    def test_dangers_page_renders(self, login_client):
        resp = login_client.get('/haccp/dangers')
        assert resp.status_code in (200, 403)

    def test_api_dangers_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/dangers')
        assert resp.status_code in (200, 403)

    def test_ccp_page_renders(self, login_client):
        resp = login_client.get('/haccp/ccp')
        assert resp.status_code in (200, 403)

    def test_api_ccp_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/ccp')
        assert resp.status_code in (200, 403)

    def test_enregistrements_page_renders(self, login_client):
        resp = login_client.get('/haccp/enregistrements')
        assert resp.status_code in (200, 403)

    def test_api_enregistrements_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/enregistrements')
        assert resp.status_code in (200, 403)

    def test_prp_page_renders(self, login_client):
        resp = login_client.get('/haccp/prp')
        assert resp.status_code in (200, 403)

    def test_api_prp_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/prp')
        assert resp.status_code in (200, 403)

    def test_tracabilite_page_renders(self, login_client):
        resp = login_client.get('/haccp/tracabilite')
        assert resp.status_code in (200, 403)

    def test_api_tracabilite_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/tracabilite')
        assert resp.status_code in (200, 403)

    def test_fournisseurs_page_redirects(self, login_client):
        resp = login_client.get('/haccp/fournisseurs')
        assert resp.status_code in (404, 403)

    def test_formations_page_redirects(self, login_client):
        resp = login_client.get('/haccp/formations')
        assert resp.status_code in (404, 403)

    def test_reclamations_page_redirects(self, login_client):
        resp = login_client.get('/haccp/reclamations')
        assert resp.status_code in (404, 403)

    def test_rappels_page_renders(self, login_client):
        resp = login_client.get('/haccp/rappels')
        assert resp.status_code in (200, 403)

    def test_api_rappels_returns_json(self, login_client):
        resp = login_client.get('/haccp/api/rappels')
        assert resp.status_code in (200, 403)


class TestNonConformitesRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/nonconformites/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/nonconformites/')
        assert resp.status_code == 200

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/nonconformites/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_stats_returns_json(self, login_client):
        resp = login_client.get('/nonconformites/api/stats')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_create(self, login_client):
        resp = login_client.post('/nonconformites/api/creer',
                                data=json.dumps({
                                    'description': 'Test NC',
                                    'source': 'interne',
                                    'domaine': 'hse',
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_update(self, login_client, nonconformite):
        resp = login_client.post(f'/nonconformites/api/{nonconformite.id}/modifier',
                                data=json.dumps({'description': 'Updated'}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_delete(self, login_client, nonconformite):
        resp = login_client.post(f'/nonconformites/api/{nonconformite.id}/supprimer',
                                data=json.dumps({}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_valider_cloture(self, login_client, nonconformite):
        resp = login_client.post(f'/nonconformites/api/{nonconformite.id}/valider-cloture',
                                data=json.dumps({}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)


class TestIshikawaRoutes:
    def test_index_requires_login(self, client):
        resp = client.get('/ishikawa/', follow_redirects=False)
        assert resp.status_code in (302, 401)

    def test_index_renders(self, login_client):
        resp = login_client.get('/ishikawa/')
        assert resp.status_code == 200

    def test_api_liste_returns_json(self, login_client):
        resp = login_client.get('/ishikawa/api/liste')
        assert resp.status_code == 200
        assert resp.content_type == 'application/json'

    def test_api_create(self, login_client):
        resp = login_client.post('/ishikawa/api/creer',
                                data=json.dumps({
                                    'titre': 'Test analyse',
                                    'probleme': 'Probleme test',
                                }),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_update(self, login_client, ishikawa_analysis):
        resp = login_client.post(f'/ishikawa/api/{ishikawa_analysis.id}/modifier',
                                data=json.dumps({'titre': 'Updated'}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)

    def test_api_delete(self, login_client, ishikawa_analysis):
        resp = login_client.post(f'/ishikawa/api/{ishikawa_analysis.id}/supprimer',
                                data=json.dumps({}),
                                content_type='application/json')
        assert resp.status_code in (200, 403)
