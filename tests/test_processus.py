import pytest
from app import db
from app.models import Processus
from datetime import date


@pytest.fixture
def processus(session, entreprise, manager_user):
    p = Processus(
        entreprise_id=entreprise.id,
        nom='Production',
        description='Processus de production',
        type_processus='operationnel',
        proprietaire_id=manager_user.id,
        entree='Matières premières',
        sortie='Produits finis',
        objectifs='Efficacité industrielle',
        statut='actif',
        date_prochaine_revu=date(2026, 6, 1),
    )
    session.add(p)
    session.commit()
    return p


class TestProcessusPages:
    def test_index_renders(self, login_client):
        resp = login_client.get('/processus/')
        assert resp.status_code == 200

    def test_bpmn_editor_renders(self, login_client, processus):
        resp = login_client.get(f'/processus/{processus.id}/bpmn')
        assert resp.status_code == 200

    def test_bpmn_editor_introuvable(self, login_client):
        resp = login_client.get('/processus/99999/bpmn')
        assert resp.status_code == 404

    def test_requires_login(self, client):
        resp = client.get('/processus/', follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestProcessusAPI:
    ENDPOINT_LISTE = '/processus/api/liste'

    def test_liste_vide(self, login_client):
        resp = login_client.get(self.ENDPOINT_LISTE)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_creer_processus(self, login_client, manager_user):
        resp = login_client.post('/processus/api/creer', json={
            'nom': 'Achat',
            'description': 'Processus achats',
            'type_processus': 'support',
            'proprietaire_id': manager_user.id,
            'entree': 'Besoin',
            'sortie': 'Commande',
            'statut': 'actif',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nom'] == 'Achat'
        assert 'id' in data

    def test_liste_apres_creation(self, login_client, processus):
        resp = login_client.get(self.ENDPOINT_LISTE)
        items = resp.get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Production'
        assert items[0]['type_processus'] == 'operationnel'

    def test_modifier_processus(self, login_client, processus):
        resp = login_client.post(f'/processus/api/{processus.id}/modifier', json={
            'nom': 'Production v2',
            'statut': 'inactif',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['nom'] == 'Production v2'

    def test_supprimer_processus(self, login_client, processus):
        resp = login_client.post(f'/processus/api/{processus.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_introuvable(self, login_client):
        resp = login_client.post('/processus/api/99999/supprimer', json={})
        assert resp.status_code == 404

    def test_stats(self, login_client, processus):
        resp = login_client.get('/processus/api/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1
        assert data['actifs'] >= 1
        assert 'a_revoir' in data


class TestProcessusBPMN:
    def test_bpmn_get_empty(self, login_client, processus):
        resp = login_client.get(f'/processus/api/{processus.id}/bpmn')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['bpmn_xml'] is None

    def test_bpmn_save(self, login_client, processus):
        resp = login_client.post(f'/processus/api/{processus.id}/bpmn', json={
            'bpmn_xml': '<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="def" targetNamespace="http://bpmn.io"><process id="Process_1" isExecutable="false"><startEvent id="StartEvent_1" /></process></definitions>',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_bpmn_get_after_save(self, login_client, processus):
        login_client.post(f'/processus/api/{processus.id}/bpmn', json={
            'bpmn_xml': '<?xml version="1.0" encoding="UTF-8"?><definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" id="def" targetNamespace="http://bpmn.io"><process id="Process_1" isExecutable="false"><startEvent id="StartEvent_1" /></process></definitions>',
        })
        resp = login_client.get(f'/processus/api/{processus.id}/bpmn')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['bpmn_xml'] is not None
        assert '<definitions' in data['bpmn_xml']

    def test_bpmn_generate(self, login_client, processus):
        resp = login_client.post(f'/processus/api/{processus.id}/bpmn/generate', json={})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['bpmn_xml'] is not None
