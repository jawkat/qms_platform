import pytest
import json
from app import db
from datetime import date

@pytest.fixture
def entreprise(entreprise):
    entreprise.modules_actifs = [
        'fournisseurs', 'environnement', 'maintenance', 'laboratoire',
        'planification', 'reunions', 'rh_qhse', 'connaissances', 'urgences',
        'hse', 'qualite', 'haccp', 'ged',
    ]
    db.session.commit()
    return entreprise

# =============================================================================
# FOURNISSEURS
# =============================================================================
from app.models import Fournisseur

@pytest.fixture
def fournisseur(session, entreprise):
    f = Fournisseur(
        entreprise_id=entreprise.id,
        nom='Fournitures Pro',
        contact='contact@fournitures-pro.ma',
        telephone='+212600000001',
        produit='Matières premières',
        domaine='hse',
        statut='actif',
    )
    session.add(f)
    session.commit()
    return f

class TestFournisseurs:
    def test_index_renders(self, login_client):
        resp = login_client.get('/fournisseurs/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/fournisseurs/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/fournisseurs/api/creer',
                                data=json.dumps({'nom': 'Test Fournisseur'}),
                                content_type='application/json')
        assert resp.status_code in (200, 201, 403)

    def test_liste(self, login_client, fournisseur):
        items = login_client.get('/fournisseurs/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Fournitures Pro'

    def test_modifier(self, login_client, fournisseur):
        resp = login_client.post(f'/fournisseurs/api/{fournisseur.id}/modifier',
                                  json={'statut': 'inactif'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('statut') == 'inactif' or data.get('success') is True

    def test_supprimer(self, login_client, fournisseur):
        resp = login_client.post(f'/fournisseurs/api/{fournisseur.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, fournisseur):
        data = login_client.get('/fournisseurs/api/stats').get_json()
        assert data['total'] >= 1
        assert data['actifs'] >= 1

    def test_evaluer(self, login_client, fournisseur):
        resp = login_client.post(f'/fournisseurs/api/{fournisseur.id}/evaluer', json={
            'note': 4, 'commentaire': 'Bon fournisseur',
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True


# =============================================================================
# ENVIRONNEMENT
# =============================================================================
from app.models import AspectEnvironnemental

@pytest.fixture
def aspect(session, entreprise):
    a = AspectEnvironnemental(
        entreprise_id=entreprise.id,
        nom='Rejets atmosphériques',
        categorie='emission',
        impact='Pollution air',
        gravite='forte',
        statut='actif',
    )
    session.add(a)
    session.commit()
    return a

class TestEnvironnement:
    def test_index_renders(self, login_client):
        resp = login_client.get('/environnement/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/environnement/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/environnement/api/creer', json={
            'nom': 'Déchets chimiques', 'categorie': 'dechets',
            'impact': 'Toxicité', 'gravite': 'critique',
            'statut': 'actif',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, aspect):
        items = login_client.get('/environnement/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Rejets atmosphériques'

    def test_modifier(self, login_client, aspect):
        resp = login_client.post(f'/environnement/api/{aspect.id}/modifier',
                                  json={'gravite': 'moyenne'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, aspect):
        resp = login_client.post(f'/environnement/api/{aspect.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, aspect):
        data = login_client.get('/environnement/api/stats').get_json()
        assert data['total_aspects'] >= 1


# =============================================================================
# MAINTENANCE
# =============================================================================
from app.models import EquipementMaintenance

@pytest.fixture
def equipement(session, entreprise):
    e = EquipementMaintenance(
        entreprise_id=entreprise.id,
        nom='Presse hydraulique',
        reference='PR-001',
        localisation='Atelier A',
        categorie='machine',
        statut='actif',
        date_prochaine_maintenance=date(2026, 7, 1),
        frequence_maintenance='mensuel',
    )
    session.add(e)
    session.commit()
    return e

class TestMaintenance:
    def test_index_renders(self, login_client):
        resp = login_client.get('/maintenance/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/maintenance/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/maintenance/api/creer', json={
            'nom': 'Compresseur', 'reference': 'CP-001',
            'localisation': 'Atelier B', 'categorie': 'machine',
            'statut': 'actif', 'frequence_maintenance': 'trimestriel',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, equipement):
        items = login_client.get('/maintenance/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Presse hydraulique'

    def test_modifier(self, login_client, equipement):
        resp = login_client.post(f'/maintenance/api/{equipement.id}/modifier',
                                  json={'statut': 'en_panne'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, equipement):
        resp = login_client.post(f'/maintenance/api/{equipement.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, equipement):
        data = login_client.get('/maintenance/api/stats').get_json()
        assert data['total'] >= 1
        assert 'actifs' in data
        assert 'en_panne' in data


# =============================================================================
# LABORATOIRE
# =============================================================================
from app.models import PlanAnalyse

@pytest.fixture
def plan_analyse(session, entreprise):
    p = PlanAnalyse(
        entreprise_id=entreprise.id,
        nom='Analyse eau',
        produit_concerne='Eau potable',
        parametre='pH',
        methode='Electrochimie',
        frequence='hebdomadaire',
        seuil_min=6.5, seuil_max=8.5, unite='pH',
        statut='actif',
    )
    session.add(p)
    session.commit()
    return p

class TestLaboratoire:
    def test_index_renders(self, login_client):
        resp = login_client.get('/laboratoire/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/laboratoire/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/laboratoire/api/creer', json={
            'nom': 'Analyse lait', 'produit_concerne': 'Lait cru',
            'parametre': 'Matière grasse', 'methode': 'Gerber',
            'frequence': 'quotidien', 'seuil_min': 30, 'seuil_max': 50,
            'unite': 'g/L', 'statut': 'actif',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, plan_analyse):
        items = login_client.get('/laboratoire/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Analyse eau'

    def test_modifier(self, login_client, plan_analyse):
        resp = login_client.post(f'/laboratoire/api/{plan_analyse.id}/modifier',
                                  json={'statut': 'inactif'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, plan_analyse):
        resp = login_client.post(f'/laboratoire/api/{plan_analyse.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, plan_analyse):
        data = login_client.get('/laboratoire/api/stats').get_json()
        assert data['plans'] >= 1
        assert 'echantillons' in data
        assert 'resultats' in data


# =============================================================================
# PLANIFICATION
# =============================================================================
from app.models import EvenementPlanification

@pytest.fixture
def evenement(session, entreprise):
    e = EvenementPlanification(
        entreprise_id=entreprise.id,
        titre='Audit interne QHSE',
        type_evenement='audit',
        date_debut=date(2026, 7, 15),
        date_fin=date(2026, 7, 16),
        lieu='Salle de réunion',
        responsable='Jean Dupont',
        statut='planifie',
    )
    session.add(e)
    session.commit()
    return e

class TestPlanification:
    def test_index_renders(self, login_client):
        resp = login_client.get('/planification/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/planification/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/planification/api/creer', json={
            'titre': 'Formation HSE',
            'type_evenement': 'formation',
            'date_debut': '2026-08-01T09:00:00',
            'date_fin': '2026-08-01T17:00:00',
            'statut': 'planifie',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, evenement):
        items = login_client.get('/planification/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Audit interne QHSE'

    def test_modifier(self, login_client, evenement):
        resp = login_client.post(f'/planification/api/{evenement.id}/modifier',
                                  json={'statut': 'termine'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, evenement):
        resp = login_client.post(f'/planification/api/{evenement.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, evenement):
        data = login_client.get('/planification/api/stats').get_json()
        assert data['total'] >= 1

    def test_calendrier(self, login_client, evenement):
        data = login_client.get('/planification/api/calendrier').get_json()
        assert len(data) >= 1
        assert data[0]['title'] == 'Audit interne QHSE'


# =============================================================================
# REUNIONS
# =============================================================================
from app.models import Reunion

@pytest.fixture
def reunion(session, entreprise):
    r = Reunion(
        entreprise_id=entreprise.id,
        titre='Revue de direction',
        type_reunion='revue_direction',
        date_reunion=date(2026, 7, 1),
        lieu='Salle conférence',
        organisateur='Directeur qualité',
        statut='planifiee',
    )
    session.add(r)
    session.commit()
    return r

class TestReunions:
    def test_index_renders(self, login_client):
        resp = login_client.get('/reunions/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/reunions/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/reunions/api/creer', json={
            'titre': 'Réunion sécurité',
            'type_reunion': 'securite',
            'date_reunion': '2026-07-15T10:00:00',
            'statut': 'planifiee',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, reunion):
        items = login_client.get('/reunions/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Revue de direction'

    def test_modifier(self, login_client, reunion):
        resp = login_client.post(f'/reunions/api/{reunion.id}/modifier',
                                  json={'statut': 'terminee'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, reunion):
        resp = login_client.post(f'/reunions/api/{reunion.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, reunion):
        data = login_client.get('/reunions/api/stats').get_json()
        assert data['total'] >= 1
        assert 'a_venir' in data
        assert 'actions_ouvertes' in data


# =============================================================================
# RH QHSE
# =============================================================================
from app.models import EmployeQHSE

@pytest.fixture
def employe_qhse(session, entreprise, manager_user):
    e = EmployeQHSE(
        entreprise_id=entreprise.id,
        utilisateur_id=manager_user.id,
        matricule='EMP-001',
        poste='Responsable qualité',
        department='Qualité',
        date_embauche=date(2024, 1, 15),
        statut='actif',
    )
    session.add(e)
    session.commit()
    return e

class TestRHQHSE:
    def test_index_renders(self, login_client):
        resp = login_client.get('/rh-qhse/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/rh-qhse/api/liste').get_json() == []

    def test_creer(self, login_client, manager_user):
        resp = login_client.post('/rh-qhse/api/creer', json={
            'utilisateur_id': manager_user.id,
            'matricule': 'EMP-002',
            'poste': 'Technicien HSE',
            'department': 'HSE',
            'date_embauche': '2025-03-01',
            'statut': 'actif',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, employe_qhse):
        items = login_client.get('/rh-qhse/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['matricule'] == 'EMP-001'

    def test_modifier(self, login_client, employe_qhse):
        resp = login_client.post(f'/rh-qhse/api/{employe_qhse.id}/modifier',
                                  json={'poste': 'Directeur qualité'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, employe_qhse):
        resp = login_client.post(f'/rh-qhse/api/{employe_qhse.id}/supprimer', json={})
        assert resp.status_code in (200, 204)

    def test_stats(self, login_client, employe_qhse):
        data = login_client.get('/rh-qhse/api/stats').get_json()
        assert data['total'] >= 1
        assert data['actifs'] >= 1


# =============================================================================
# CONNAISSANCES
# =============================================================================
from app.models import REX

@pytest.fixture
def rex(session, entreprise):
    r = REX(
        entreprise_id=entreprise.id,
        titre='Incident chimique',
        description='Déversement acide',
        categorie='incident',
        contexte='Laboratoire',
        lecons_apprises='Former le personnel',
        auteur='Jean Dupont',
        statut='publie',
    )
    session.add(r)
    session.commit()
    return r

class TestConnaissances:
    def test_index_renders(self, login_client):
        resp = login_client.get('/connaissances/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/connaissances/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/connaissances/api/creer', json={
            'titre': 'Bonnes pratiques soudure',
            'description': 'Procédure recommandée',
            'categorie': 'best_practice',
            'contexte': 'Atelier',
            'auteur': 'Marie',
            'statut': 'brouillon',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, rex):
        items = login_client.get('/connaissances/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['titre'] == 'Incident chimique'

    def test_modifier(self, login_client, rex):
        resp = login_client.post(f'/connaissances/api/{rex.id}/modifier',
                                  json={'statut': 'brouillon'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, rex):
        resp = login_client.post(f'/connaissances/api/{rex.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, rex):
        data = login_client.get('/connaissances/api/stats').get_json()
        assert data['rex_total'] >= 1
        assert 'rex_publies' in data
        assert 'faq' in data


# =============================================================================
# URGENCES
# =============================================================================
from app.models import PlanUrgence

@pytest.fixture
def plan_urgence(session, entreprise):
    p = PlanUrgence(
        entreprise_id=entreprise.id,
        nom='Plan incendie',
        type_urgence='incendie',
        description='Évacuation bâtiment A',
        procedures='1. Alerter 2. Évacuer 3. Rassemblement',
        statut='actif',
    )
    session.add(p)
    session.commit()
    return p

class TestUrgences:
    def test_index_renders(self, login_client):
        resp = login_client.get('/urgences/')
        assert resp.status_code == 200

    def test_liste_vide(self, login_client):
        assert login_client.get('/urgences/api/liste').get_json() == []

    def test_creer(self, login_client):
        resp = login_client.post('/urgences/api/creer', json={
            'nom': 'Plan pollution',
            'type_urgence': 'pollution',
            'description': 'Contamination rivière',
            'statut': 'actif',
        })
        assert resp.status_code in (200, 201)

    def test_liste(self, login_client, plan_urgence):
        items = login_client.get('/urgences/api/liste').get_json()
        assert len(items) == 1
        assert items[0]['nom'] == 'Plan incendie'

    def test_modifier(self, login_client, plan_urgence):
        resp = login_client.post(f'/urgences/api/{plan_urgence.id}/modifier',
                                  json={'statut': 'inactif'})
        assert resp.status_code == 200

    def test_supprimer(self, login_client, plan_urgence):
        resp = login_client.post(f'/urgences/api/{plan_urgence.id}/supprimer', json={})
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_stats(self, login_client, plan_urgence):
        data = login_client.get('/urgences/api/stats').get_json()
        assert data['plans'] >= 1
        assert 'exercices' in data
        assert 'incidents_ouverts' in data
