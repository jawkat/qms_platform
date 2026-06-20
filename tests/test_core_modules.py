import pytest
from app import db
from app.change_management.models import ChangeRequest
from app.workflow_engine.models import WorkflowModele, WorkflowEtape, WorkflowInstance
from datetime import date, datetime


# =============================================================================
# CHANGE MANAGEMENT
# =============================================================================

@pytest.fixture
def change_request(session, entreprise, manager_user):
    c = ChangeRequest(
        entreprise_id=entreprise.id,
        reference='CR-202606-0001',
        titre='Migration serveur',
        description='Migration vers nouveau serveur',
        type_changement='processus',
        priorite='haute',
        statut='approuve',
        demandeur_id=manager_user.id,
        date_demande=date(2026, 6, 1),
        date_souhaitee=date(2026, 6, 15),
        raison='Amélioration performance',
    )
    session.add(c)
    session.commit()
    return c


class TestChangeManagement:
    def test_index_renders(self, login_client):
        resp = login_client.get('/change-management/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        resp = login_client.get('/change-management/api/liste')
        assert resp.get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/change-management/api/creer', json={
            'titre': 'Nouveau process',
            'description': 'Description du changement',
            'type_changement': 'organisationnel',
            'priorite': 'basse',
            'statut': 'brouillon',
            'date_demande': '2026-06-10',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'id' in data

    def test_liste(self, login_client, change_request):
        items = login_client.get('/change-management/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Migration serveur'

    def test_modifier(self, login_client, change_request):
        resp = login_client.post(f'/change-management/api/{change_request.id}/modifier',
                                  json={'statut': 'en_realisation'})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer(self, login_client, change_request):
        resp = login_client.post(f'/change-management/api/{change_request.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, change_request):
        data = login_client.get('/change-management/api/stats').get_json()
        assert data['total'] >= 1
        assert data['approuve'] >= 1


# =============================================================================
# WORKFLOW ENGINE
# =============================================================================

@pytest.fixture
def workflow_modele(session, entreprise):
    m = WorkflowModele(
        entreprise_id=entreprise.id,
        nom='Validation document',
        module_cible='documents',
        statut='actif',
    )
    session.add(m)
    session.flush()
    e = WorkflowEtape(
        modele_id=m.id,
        nom='Validation',
        ordre=1,
        action_requise='approuver',
    )
    session.add(e)
    session.commit()
    return m


class TestWorkflowEngine:
    def test_index_renders(self, login_client):
        resp = login_client.get('/workflow-engine/')
        assert resp.status_code == 200

    def test_api_modeles(self, login_client, workflow_modele):
        resp = login_client.get('/workflow-engine/api/modeles')
        assert resp.status_code == 200
        items = resp.get_json()
        assert len(items) >= 1
        assert items[0]['nom'] == 'Validation document'

    def test_creer_modele(self, login_client):
        resp = login_client.post('/workflow-engine/api/modeles/creer', json={
            'nom': 'Achat validation',
            'module_cible': 'documents',
            'etapes': [{'nom': 'Validation chef', 'action_requise': 'approuver'}],
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, workflow_modele):
        data = login_client.get('/workflow-engine/api/stats').get_json()
        assert data['modeles'] >= 1
