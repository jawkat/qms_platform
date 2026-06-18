import pytest
from datetime import date, datetime
from app import db
from app.models import (
    Entreprise, Utilisateur, Role, Permission, RolePermission,
    ActionCorrective, ActionStatusEnum, ProofMaster, Audit,
    Indicateur, IndicateurValeur, Ticket,
    Risque, ReclamationClient, Fournisseur, Formation, Equipement,
    ControleQualite, RevueDirection, NonConformiteQualite,
)


class TestEntreprise:
    def test_create_entreprise(self, session):
        ent = Entreprise(nom='Acme', modules_actifs=['hse'])
        session.add(ent)
        session.commit()
        assert ent.id is not None
        assert ent.nom == 'Acme'
        assert ent.taille == 'PME'
        assert ent.pays == 'Maroc'

    def test_entreprise_default_values(self, session):
        ent = Entreprise(nom='Test')
        session.add(ent)
        session.commit()
        assert ent.modules_actifs == ['hse']
        assert ent.abonnement_type == 'trial'
        assert ent.abonnement_paye is False


class TestUtilisateur:
    def test_create_user(self, session, entreprise, role_manager):
        user = Utilisateur(
            nom='Dupont',
            prenom='Jean',
            email='jean@test.com',
            role_id=role_manager.id,
            entreprise_id=entreprise.id,
        )
        user.set_password('secret')
        session.add(user)
        session.commit()
        assert user.id is not None
        assert user.check_password('secret') is True
        assert user.check_password('wrong') is False

    def test_user_has_permission_systeme(self, session, admin_user):
        perm = Permission(code='users.create', description='Create users', module='users')
        session.add(perm)
        session.commit()
        assert admin_user.has_permission('users.create') is True

    def test_user_no_role_no_permission(self, session, entreprise):
        user = Utilisateur(
            nom='NoRole', prenom='User', email='norole@test.com',
            entreprise_id=entreprise.id,
        )
        user.set_password('pass')
        session.add(user)
        session.commit()
        assert user.has_permission('anything') is False

    def test_user_get_id_returns_string(self, session, manager_user):
        assert isinstance(manager_user.get_id(), str)
        assert manager_user.get_id() == str(manager_user.id)


class TestRole:
    def test_create_role(self, session):
        role = Role(nom='TestRole', description='A test role')
        session.add(role)
        session.commit()
        assert role.id is not None
        assert role.est_systeme is False
        assert role.personnalisable is True


class TestPermission:
    def test_create_permission(self, session):
        perm = Permission(code='actions.voir', description='View actions', module='actions')
        session.add(perm)
        session.commit()
        assert perm.id is not None
        assert perm.code == 'actions.voir'


class TestRolePermission:
    def test_assign_permission_to_role(self, session, role_manager):
        perm = Permission.query.filter_by(code='actions.creer').first()
        if not perm:
            perm = Permission(code='actions.creer', description='Create actions', module='actions')
            session.add(perm)
            session.flush()
        existing = RolePermission.query.filter_by(
            role_id=role_manager.id, permission_id=perm.id
        ).first()
        if existing:
            rp = existing
        else:
            rp = RolePermission(role_id=role_manager.id, permission_id=perm.id, autorise=True)
            session.add(rp)
        session.commit()
        assert rp.id is not None


class TestActionCorrective:
    def test_create_action(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Fix issue',
            type_action='corrective',
            priorite='haute',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date.today(),
        )
        session.add(action)
        session.commit()
        assert action.id is not None
        assert action.statut == 'A_FAIRE'

    def test_action_statut_label(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Test',
            statut='EN_COURS',
            responsable_id=manager_user.id,
        )
        session.add(action)
        session.commit()
        assert action.statut_label == 'En cours'

    def test_action_statut_label_unknown(self, session, entreprise, manager_user):
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            description='Test',
            statut='UNKNOWN_STATUS',
            responsable_id=manager_user.id,
        )
        session.add(action)
        session.commit()
        assert action.statut_label == 'UNKNOWN_STATUS'

    def test_action_status_enum_choices(self):
        choices = ActionStatusEnum.choices()
        assert ('A_FAIRE', 'À faire') in choices
        assert len(choices) == 5


class TestProofMaster:
    def test_create_proof(self, session, entreprise):
        proof = ProofMaster(
            entreprise_id=entreprise.id,
            nom_fichier='report.pdf',
            type='pdf',
            chemin='preuves/1/report.pdf',
            hash_fichier='abc123',
            statut='ACTIF',
        )
        session.add(proof)
        session.commit()
        assert proof.id is not None
        assert proof.statut == 'ACTIF'
        assert proof.version == '1'


class TestAudit:
    def test_create_audit(self, session, entreprise, auditeur_user):
        audit = Audit(
            entreprise_id=entreprise.id,
            type='interne',
            date_audit=date.today(),
            auditeur_id=auditeur_user.id,
            resultat_global='conforme',
        )
        session.add(audit)
        session.commit()
        assert audit.id is not None


class TestIndicateur:
    def test_create_indicateur(self, session):
        ind = Indicateur(
            nom='KPI 1',
            formule='a / b',
            periode='mensuel',
        )
        session.add(ind)
        session.commit()
        assert ind.id is not None

    def test_create_indicateur_valeur(self, session, entreprise, indicateur):
        val = IndicateurValeur(
            indicateur_id=indicateur.id,
            entreprise_id=entreprise.id,
            valeur=75.0,
            date_calcul=date.today(),
        )
        session.add(val)
        session.commit()
        assert val.id is not None
        assert val.valeur == 75.0


class TestTicket:
    def test_create_ticket(self, session, entreprise, manager_user):
        t = Ticket(
            reference='TKT-0099',
            sujet='Bug report',
            type='technique',
            statut='OUVERT',
            nom_contact='Test',
            email_contact='test@test.com',
            entreprise_id=entreprise.id,
            cree_par_id=manager_user.id,
        )
        session.add(t)
        session.commit()
        assert t.id is not None
        assert t.reference == 'TKT-0099'


class TestQualityModels:
    def test_risque_ipr(self, session, entreprise, manager_user):
        risque = Risque(
            entreprise_id=entreprise.id,
            designation='Fire risk',
            gravite=4,
            probabilite=3,
            detection=2,
            responsable_id=manager_user.id,
        )
        session.add(risque)
        session.commit()
        assert risque.ipr == 24

    def test_risque_ipr_default(self, session, entreprise, manager_user):
        risque = Risque(
            entreprise_id=entreprise.id,
            designation='Default risk',
            responsable_id=manager_user.id,
        )
        session.add(risque)
        session.commit()
        assert risque.ipr == 1

    def test_reclamation_client(self, session, entreprise, manager_user):
        rc = ReclamationClient(
            entreprise_id=entreprise.id,
            date_reclamation=date.today(),
            client='Client A',
            description='Defective product',
            responsable_id=manager_user.id,
        )
        session.add(rc)
        session.commit()
        assert rc.id is not None

    def test_fournisseur(self, session, entreprise):
        f = Fournisseur(
            entreprise_id=entreprise.id,
            nom='Supplier X',
            produit='Raw material',
            evaluation=4,
        )
        session.add(f)
        session.commit()
        assert f.id is not None

    def test_formation(self, session, entreprise):
        f = Formation(
            entreprise_id=entreprise.id,
            titre='Safety Training',
            formateur='Expert',
            duree_heures=8.0,
        )
        session.add(f)
        session.commit()
        assert f.id is not None

    def test_equipement(self, session, entreprise):
        e = Equipement(
            entreprise_id=entreprise.id,
            nom='Fire Extinguisher',
            modele='FE-200',
            numero_serie='SN-001',
        )
        session.add(e)
        session.commit()
        assert e.id is not None

    def test_controle_qualite(self, session, entreprise):
        cq = ControleQualite(
            entreprise_id=entreprise.id,
            date_controle=date.today(),
            produit='Product A',
            resultat='conforme',
        )
        session.add(cq)
        session.commit()
        assert cq.id is not None

    def test_revue_direction(self, session, entreprise):
        rd = RevueDirection(
            entreprise_id=entreprise.id,
            date_revue=date.today(),
            participants='Director, Manager',
            decisions='Improve process X',
        )
        session.add(rd)
        session.commit()
        assert rd.id is not None

    def test_non_conformite_qualite(self, session, entreprise, manager_user):
        nc = NonConformiteQualite(
            entreprise_id=entreprise.id,
            date_nc=date.today(),
            reference='NC-001',
            produit_processus='Process Y',
            description='Deviation detected',
            responsable_id=manager_user.id,
        )
        session.add(nc)
        session.commit()
        assert nc.id is not None
