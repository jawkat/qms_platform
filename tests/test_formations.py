import pytest
from app import db
from app.models.partages import Formation
from app.models.competence import Competence, FormationParticipant, EmployeCompetence
from app.models.auth import Utilisateur
from datetime import date, datetime


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def formation_data():
    return {
        'titre': 'Formation HSE',
        'theme': 'Sécurité',
        'formateur': 'Jean Dupont',
        'participants': '12',
        'duree_heures': 7.0,
        'date_formation': '2026-01-15',
        'evaluation': 'Post-test',
        'statut': 'planifiee',
    }


@pytest.fixture
def formation(session, entreprise):
    """Créé une formation de test (entreprise par défaut avec modules actifs)."""
    f = Formation(
        entreprise_id=entreprise.id,
        domaine='hse',
        titre='Formation Sécurité',
        theme='Incendie',
        formateur='Jean Dupont',
        participants='10',
        date_formation=date(2026, 3, 1),
        duree_heures=7.0,
        type_formation='interne',
        evaluation='QCM',
        statut='planifiee',
        annee=2026,
    )
    session.add(f)
    session.commit()
    return f


@pytest.fixture
def competence(session, entreprise):
    c = Competence(
        entreprise_id=entreprise.id,
        nom='Gestes de premier secours',
        description='Savoir réagir en cas d\'urgence',
        domaine='hse',
    )
    session.add(c)
    session.commit()
    return c


@pytest.fixture
def formation_participant(session, formation, manager_user):
    fp = FormationParticipant(
        formation_id=formation.id,
        utilisateur_id=manager_user.id,
        statut='inscrit',
        evaluation_score=85.0,
        evaluation_commentaire='Bon travail',
        certifie=True,
        date_certification=date(2026, 4, 1),
        date_expiration_certification=date(2027, 4, 1),
    )
    session.add(fp)
    session.commit()
    return fp


@pytest.fixture
def employe_competence(session, entreprise, competence, manager_user):
    ec = EmployeCompetence(
        entreprise_id=entreprise.id,
        utilisateur_id=manager_user.id,
        competence_id=competence.id,
        niveau_requis=3,
        niveau_actuel=2,
        date_evaluation=date(2026, 2, 15),
        evalue_par_id=manager_user.id,
        notes='En progrès',
    )
    session.add(ec)
    session.commit()
    return ec


@pytest.fixture
def login_formation_client(client, manager_user):
    """Client connecté avec permissions formations (via rôle Manager)."""
    client.post('/users/login', data={
        'email': manager_user.email,
        'password': 'manager123',
    }, follow_redirects=True)
    return client


# =============================================================================
# Pages
# =============================================================================

class TestFormationsPages:
    def test_index_renders(self, login_formation_client):
        resp = login_formation_client.get('/formations/')
        assert resp.status_code == 200

    def test_participants_renders(self, login_formation_client):
        resp = login_formation_client.get('/formations/participants')
        assert resp.status_code == 200

    def test_matrice_renders(self, login_formation_client):
        resp = login_formation_client.get('/formations/matrice')
        assert resp.status_code == 200

    def test_certifications_renders(self, login_formation_client):
        resp = login_formation_client.get('/formations/certifications')
        assert resp.status_code == 200

    def test_requires_login(self, client):
        resp = client.get('/formations/', follow_redirects=False)
        assert resp.status_code in (302, 401)


# =============================================================================
# CRUD Formations
# =============================================================================

class TestFormationsAPI:
    ENDPOINT_LISTE = '/formations/api/liste'
    ENDPOINT_CREER = '/formations/api/creer'

    def test_liste_vide(self, login_formation_client):
        resp = login_formation_client.get(self.ENDPOINT_LISTE)
        assert resp.status_code == 200
        assert resp.is_json
        assert resp.get_json() == []

    def test_creer_formation(self, login_formation_client, formation_data):
        resp = login_formation_client.post(self.ENDPOINT_CREER,
                                           json=formation_data)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'id' in data

    def test_liste_apres_creation(self, login_formation_client, formation_data):
        login_formation_client.post(self.ENDPOINT_CREER, json=formation_data)
        resp = login_formation_client.get(self.ENDPOINT_LISTE)
        items = resp.get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Formation HSE'

    def test_modifier_formation(self, login_formation_client, formation):
        resp = login_formation_client.post(
            f'/formations/api/{formation.id}/modifier',
            json={'titre': 'Formation Modifiée', 'statut': 'realisee'},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_formation(self, login_formation_client, formation):
        resp = login_formation_client.post(
            f'/formations/api/{formation.id}/supprimer',
            json={},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_formation_introuvable(self, login_formation_client):
        resp = login_formation_client.post('/formations/api/99999/supprimer', json={})
        assert resp.status_code == 404

    def test_creer_sans_permission(self, client, formation_data):
        resp = client.post(self.ENDPOINT_CREER, json=formation_data,
                           follow_redirects=False)
        assert resp.status_code in (302, 401)


# =============================================================================
# Compétences
# =============================================================================

class TestCompetencesAPI:
    def test_liste_competences(self, login_formation_client, competence):
        resp = login_formation_client.get('/formations/api/competences')
        assert resp.status_code == 200
        items = resp.get_json()
        assert any(c['nom'] == 'Gestes de premier secours' for c in items)

    def test_creer_competence(self, login_formation_client):
        resp = login_formation_client.post('/formations/api/competences/create', json={
            'nom': 'Soudure', 'description': 'Soudure à l\'arc', 'domaine': 'qualite',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_competence(self, login_formation_client, competence):
        resp = login_formation_client.post(
            f'/formations/api/competences/{competence.id}/delete', json={},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True


# =============================================================================
# Participants
# =============================================================================

class TestParticipantsAPI:
    def test_liste_participants_vide(self, login_formation_client, formation):
        resp = login_formation_client.get(f'/formations/api/participants/{formation.id}')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_inscrire_participant(self, login_formation_client, formation, manager_user):
        resp = login_formation_client.post('/formations/api/participants/create', json={
            'formation_id': formation.id,
            'utilisateur_id': manager_user.id,
            'statut': 'inscrit',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_inscription_doublon_refusee(self, login_formation_client, formation,
                                          manager_user, formation_participant):
        resp = login_formation_client.post('/formations/api/participants/create', json={
            'formation_id': formation.id,
            'utilisateur_id': manager_user.id,
        })
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_modifier_participant(self, login_formation_client, formation_participant):
        resp = login_formation_client.post(
            f'/formations/api/participants/{formation_participant.id}/update',
            json={'statut': 'present', 'evaluation_score': 95.0},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_participant(self, login_formation_client, formation_participant):
        resp = login_formation_client.post(
            f'/formations/api/participants/{formation_participant.id}/delete', json={},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True


# =============================================================================
# Matrice Compétences
# =============================================================================

class TestMatriceAPI:
    def test_liste_matrice_vide(self, login_formation_client):
        resp = login_formation_client.get('/formations/api/matrice')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_creer_evaluation(self, login_formation_client, competence, manager_user):
        resp = login_formation_client.post('/formations/api/matrice/create', json={
            'utilisateur_id': manager_user.id,
            'competence_id': competence.id,
            'niveau_requis': 3,
            'niveau_actuel': 2,
            'date_evaluation': '2026-02-15',
            'evalue_par_id': manager_user.id,
            'notes': 'Bon niveau',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_creer_evaluation_doublon(self, login_formation_client, competence,
                                       manager_user, employe_competence):
        resp = login_formation_client.post('/formations/api/matrice/create', json={
            'utilisateur_id': manager_user.id,
            'competence_id': competence.id,
        })
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_modifier_evaluation(self, login_formation_client, employe_competence):
        resp = login_formation_client.post(
            f'/formations/api/matrice/{employe_competence.id}/update',
            json={'niveau_actuel': 3, 'notes': 'Expert'},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_supprimer_evaluation(self, login_formation_client, employe_competence):
        resp = login_formation_client.post(
            f'/formations/api/matrice/{employe_competence.id}/delete', json={},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True


# =============================================================================
# Certifications
# =============================================================================

class TestCertificationsAPI:
    def test_liste_certifications(self, login_formation_client, formation_participant):
        resp = login_formation_client.get('/formations/api/certifications')
        assert resp.status_code == 200
        items = resp.get_json()
        assert len(items) >= 1
        assert items[0]['score'] == 85.0
        assert items[0]['utilisateur_id'] == formation_participant.utilisateur_id

    def test_liste_certifications_vide(self, login_formation_client):
        resp = login_formation_client.get('/formations/api/certifications')
        assert resp.status_code == 200
        assert resp.get_json() == []


# =============================================================================
# Stats & Calendrier
# =============================================================================

class TestStatsEtCalendrier:
    def test_stats(self, login_formation_client, formation, formation_participant):
        resp = login_formation_client.get('/formations/api/stats')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_formations' in data
        assert 'planifiees' in data
        assert 'certifies' in data
        assert data['total_formations'] >= 1

    def test_calendrier(self, login_formation_client, formation):
        resp = login_formation_client.get('/formations/api/calendrier')
        assert resp.status_code == 200
        items = resp.get_json()
        assert len(items) == 1
        assert items[0]['title'] == 'Formation Sécurité'
        assert 'start' in items[0]
        assert 'color' in items[0]
