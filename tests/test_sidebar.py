import pytest
from app import db
from app.models.entreprise import Entreprise
from datetime import date


SIDEBAR_SECTION_MAP = {
    # module_name -> (section_id, section_title)
    'qualite': ('qualite', 'Qualité / ISO 9001'),
    'pilotage': ('pilotage', 'Pilotage & Transversal'),
    'performance': ('performance', 'Performance & KPI'),
    'nc_capa': ('nc_capa', 'NC & CAPA'),
    'audits': ('audits', 'Audits'),
    'processus': ('processus', 'Processus & Workflows'),
    'veille': ('veille', 'Veille réglementaire'),
    'formations': ('formations', 'Formations & Compétences'),
    'rh_qhse': ('rh_qhse', 'RH QHSE'),
    'connaissances': ('connaissances', 'Connaissances'),
    'fournisseurs': ('fournisseurs', 'Fournisseurs & Achats'),
    'planification': ('planification', 'Planification'),
    'reunions': ('reunions', 'Réunions & Revues'),
    'maintenance': ('maintenance', 'Maintenance'),
    'laboratoire': ('laboratoire', 'Laboratoire'),
    'hse': ('hse', 'HSE / ISO 45001'),
    'environnement': ('environnement', 'Environnement / ISO 14001'),
    'haccp': ('haccp', 'HACCP / ISO 22000'),
    'urgences': ('urgences', 'Gestion des urgences'),
}

ALL_MODULE_NAMES = list(SIDEBAR_SECTION_MAP.keys())


@pytest.fixture
def entreprise_all_modules(session):
    ent = Entreprise(
        nom='Test All Modules',
        taille='PME',
        pays='Maroc',
        modules_actifs=ALL_MODULE_NAMES,
        abonnement_type='professional',
        abonnement_paye=True,
        statut='active',
        date_inscription=date.today(),
    )
    session.add(ent)
    session.commit()
    return ent


@pytest.fixture
def entreprise_no_modules(session):
    ent = Entreprise(
        nom='Test No Modules',
        taille='PME',
        pays='Maroc',
        modules_actifs=[],
        abonnement_type='free',
        abonnement_paye=True,
        statut='active',
        date_inscription=date.today(),
    )
    session.add(ent)
    session.commit()
    return ent


class TestSidebarSections:
    """Tests unitaires pour get_sidebar_sections()."""

    def test_general_toujours_present(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            ids = {s['id'] for s in sections}
            assert 'general' in ids

    def test_compte_toujours_present(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            ids = {s['id'] for s in sections}
            assert 'compte' in ids

    def test_ged_ajoute_documents_dans_general(self, app, session, entreprise_no_modules):
        entreprise_no_modules.modules_actifs = ['ged']
        session.commit()
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            general = next(s for s in sections if s['id'] == 'general')
            labels = [i['label'] for i in general['items'] if i['label']]
            assert 'Documents' in labels

    def test_module_inactif_aucune_section(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            section_ids = {s['id'] for s in sections}
            for mod_name, (sec_id, _) in SIDEBAR_SECTION_MAP.items():
                assert sec_id not in section_ids, f'{sec_id} ne devrait pas apparaître'

    def test_chaque_module_cree_sa_section(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            section_map = {s['id']: s for s in sections}
            for mod_name, (sec_id, sec_title) in SIDEBAR_SECTION_MAP.items():
                assert sec_id in section_map, f'Module {mod_name} devrait créer section {sec_id}'
                assert section_map[sec_id]['title'] == sec_title

    def test_toutes_sections_presentes_avec_tous_modules(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            section_ids = {s['id'] for s in sections}
            expected = {sid for _, (sid, _) in SIDEBAR_SECTION_MAP.items()} | {'general', 'compte'}
            assert section_ids == expected, f'Manque: {expected - section_ids}'

    def test_administration_reserve_systeme(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id, is_systeme=True)
            ids = {s['id'] for s in sections}
            assert 'admin' in ids
            assert 'veille_admin' in ids

    def test_administration_cachee_sans_systeme(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id, is_systeme=False)
            ids = {s['id'] for s in sections}
            assert 'admin' not in ids
            assert 'veille_admin' not in ids

    def test_ordre_sections_coherent(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            ids = [s['id'] for s in sections]
            # Les sections système arrivent en premier
            idx_general = ids.index('general')
            idx_compte = ids.index('compte')
            # Vérifier l'ordre métier: qualite avant formations, hse avant environnement, etc.
            assert ids.index('qualite') < ids.index('formations')
            assert ids.index('pilotage') < ids.index('nc_capa')
            assert ids.index('nc_capa') < ids.index('audits')
            assert ids.index('processus') < ids.index('veille')
            assert ids.index('formations') < ids.index('hse')
            assert ids.index('hse') < ids.index('environnement')
            assert ids.index('environnement') < ids.index('haccp')
            assert ids.index('haccp') < ids.index('urgences')

    def test_sans_ged_documents_absent(self, app, entreprise_no_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            general = next(s for s in sections if s['id'] == 'general')
            labels = [i['label'] for i in general['items'] if i['label']]
            assert 'Documents' not in labels

    def test_ghost_module_reclamations_ignore(self, app, session, entreprise_no_modules):
        entreprise_no_modules.modules_actifs = ['reclamations']
        session.commit()
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_no_modules.id)
            ids = {s['id'] for s in sections}
            assert 'reclamations' not in ids
            assert 'general' in ids
            assert 'compte' in ids


class TestFormationsSidebar:
    def test_quatre_items_presents(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            formation_sec = next(s for s in sections if s['id'] == 'formations')
            labels = [i['label'] for i in formation_sec['items']]
            assert labels == ['Formations', 'Participants', 'Matrice compétences', 'Certifications']

    def test_icones_correctes(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            formation_sec = next(s for s in sections if s['id'] == 'formations')
            icones = [i['icon'] for i in formation_sec['items']]
            assert icones == ['fa-graduation-cap', 'fa-users', 'fa-th-list', 'fa-certificate']

    def test_endpoints_corrects(self, app, entreprise_all_modules):
        with app.app_context():
            sections = app.plugin_manager.get_sidebar_sections(entreprise_all_modules.id)
            formation_sec = next(s for s in sections if s['id'] == 'formations')
            endpoints = [i['endpoint'] for i in formation_sec['items']]
            assert endpoints == [
                'formations.index',
                'formations.participants',
                'formations.matrice',
                'formations.certifications',
            ]
