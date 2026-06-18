import os
import tempfile
import pytest
from datetime import date, datetime

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['MAIL_SERVER'] = 'localhost'
os.environ['MAIL_PORT'] = '25'
os.environ['MAIL_USE_TLS'] = '0'
os.environ['MAIL_USERNAME'] = ''
os.environ['MAIL_PASSWORD'] = ''
os.environ['AUTO_BOOTSTRAP'] = '0'

from app import db as _db, create_app
from app.models import (
    Entreprise, Utilisateur, Role, Permission, RolePermission,
    ActionCorrective, ProofMaster, Audit,
    Indicateur, IndicateurValeur, Ticket,
)


@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['SERVER_NAME'] = 'localhost'
    return app


@pytest.fixture(scope='function')
def _db_session(app):
    """Create all tables and yield a session; drop after test."""
    with app.app_context():
        _db.create_all()
        yield _db.session
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, _db_session):
    """Test client that shares the same DB connection as _db_session."""
    with app.app_context():
        yield app.test_client()


@pytest.fixture(scope='function')
def session(_db_session):
    return _db_session


def _create_permissions(db_session):
    perm_codes = [
        'actions.voir', 'actions.creer', 'actions.modifier', 'actions.supprimer',
        'documents.voir', 'documents.creer', 'documents.modifier', 'documents.supprimer',
        'textes.voir', 'textes.creer', 'textes.modifier',
        'conformite.voir', 'conformite.evaluer',
        'qualite.voir', 'qualite.gerer_risques',
        'audit.voir', 'audit.creer',
        'indicateurs.voir', 'indicateurs.creer',
        'support.voir', 'support.creer',
        'users.voir', 'users.creer', 'users.modifier', 'users.supprimer',
        'admin.voir', 'admin.gerer',
        'secteur.voir', 'secteur.gerer',
    ]
    perms = {}
    for code in perm_codes:
        perm = Permission.query.filter_by(code=code).first()
        if not perm:
            perm = Permission(code=code, description=code, module=code.split('.')[0])
            db_session.add(perm)
            db_session.flush()
        perms[code] = perm
    return perms


@pytest.fixture
def entreprise(session):
    ent = Entreprise(
        nom='Test Corp',
        taille='PME',
        pays='Maroc',
        modules_actifs=['hse', 'qualite'],
        abonnement_type='professional',
        abonnement_paye=True,
        statut='active',
        date_inscription=date.today(),
    )
    session.add(ent)
    session.commit()
    return ent


@pytest.fixture
def role_systeme(session):
    role = Role(nom='SystemAdmin', est_systeme=True, personnalisable=False)
    session.add(role)
    session.commit()
    return role


@pytest.fixture
def role_manager(session, entreprise):
    perms = _create_permissions(session)
    role = Role(nom='Manager', est_systeme=False, personnalisable=True)
    session.add(role)
    session.flush()
    for perm in perms.values():
        rp = RolePermission(role_id=role.id, permission_id=perm.id, entreprise_id=entreprise.id, autorise=True)
        session.add(rp)
    session.commit()
    return role


@pytest.fixture
def role_auditeur(session, entreprise):
    perms = _create_permissions(session)
    role = Role(nom='Auditeur', est_systeme=False, personnalisable=True)
    session.add(role)
    session.flush()
    for perm in perms.values():
        rp = RolePermission(role_id=role.id, permission_id=perm.id, entreprise_id=entreprise.id, autorise=True)
        session.add(rp)
    session.commit()
    return role


@pytest.fixture
def admin_user(session, entreprise, role_systeme):
    user = Utilisateur(
        nom='Admin',
        prenom='Super',
        email='admin@test.com',
        role_id=role_systeme.id,
        entreprise_id=entreprise.id,
        actif=True,
    )
    user.set_password('admin123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def manager_user(session, entreprise, role_manager):
    user = Utilisateur(
        nom='Manager',
        prenom='Jean',
        email='manager@test.com',
        role_id=role_manager.id,
        entreprise_id=entreprise.id,
        actif=True,
    )
    user.set_password('manager123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def auditeur_user(session, entreprise, role_auditeur):
    user = Utilisateur(
        nom='Auditeur',
        prenom='Marie',
        email='auditeur@test.com',
        role_id=role_auditeur.id,
        entreprise_id=entreprise.id,
        actif=True,
    )
    user.set_password('auditeur123')
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def action(session, entreprise, manager_user):
    action = ActionCorrective(
        entreprise_id=entreprise.id,
        domaine='hse',
        description='Test corrective action',
        type_action='corrective',
        priorite='haute',
        statut='A_FAIRE',
        responsable_id=manager_user.id,
        date_echeance=date.today(),
        est_recurrente=False,
    )
    session.add(action)
    session.commit()
    return action


@pytest.fixture
def action_recurrente(session, entreprise, manager_user):
    action = ActionCorrective(
        entreprise_id=entreprise.id,
        domaine='hse',
        description='Periodic action',
        type_action='periodique',
        priorite='moyenne',
        statut='A_FAIRE',
        responsable_id=manager_user.id,
        date_echeance=date(2025, 6, 15),
        est_recurrente=True,
        frequence='mensuel',
    )
    session.add(action)
    session.commit()
    return action


@pytest.fixture
def proof(session, entreprise, manager_user):
    proof = ProofMaster(
        entreprise_id=entreprise.id,
        domaine='hse',
        nom_fichier='test_document.pdf',
        type='pdf',
        chemin='preuves/1/test_doc.pdf',
        taille_bytes=1024,
        hash_fichier='abc123hash',
        statut='ACTIF',
        upload_par=manager_user.id,
    )
    session.add(proof)
    session.commit()
    return proof


@pytest.fixture
def audit_record(session, entreprise, auditeur_user):
    audit = Audit(
        entreprise_id=entreprise.id,
        domaine='hse',
        type='interne',
        date_audit=date.today(),
        auditeur_id=auditeur_user.id,
        resultat_global='conforme',
        commentaire='Test audit',
    )
    session.add(audit)
    session.commit()
    return audit


@pytest.fixture
def indicateur(session):
    ind = Indicateur(
        nom='Taux de conformite',
        description='Pourcentage de conformite',
        formule='conformes / applicables * 100',
        periode='mensuel',
    )
    session.add(ind)
    session.commit()
    return ind


@pytest.fixture
def indicateur_valeur(session, entreprise, indicateur):
    val = IndicateurValeur(
        indicateur_id=indicateur.id,
        entreprise_id=entreprise.id,
        valeur=85.5,
        date_calcul=date.today(),
    )
    session.add(val)
    session.commit()
    return val


@pytest.fixture
def ticket(session, entreprise, manager_user):
    t = Ticket(
        reference='TKT-0001',
        type='technique',
        sujet='Probleme technique',
        statut='OUVERT',
        nom_contact='Test User',
        email_contact='test@test.com',
        entreprise_id=entreprise.id,
        cree_par_id=manager_user.id,
    )
    session.add(t)
    session.commit()
    return t


@pytest.fixture
def login_client(client, manager_user):
    resp = client.post('/users/login', data={
        'email': manager_user.email,
        'password': 'manager123',
    }, follow_redirects=True)
    return client


@pytest.fixture
def login_admin(client, admin_user):
    resp = client.post('/users/login', data={
        'email': admin_user.email,
        'password': 'admin123',
    }, follow_redirects=True)
    return client
