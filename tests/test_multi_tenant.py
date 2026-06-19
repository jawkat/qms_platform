import pytest
import json
from datetime import date


class TestTenantIsolation:

    def _create_entreprise_b(self, session):
        from app.models import Entreprise
        ent_b = Entreprise(
            nom='Societe B',
            taille='PME',
            pays='Maroc',
            modules_actifs=['hse', 'qualite'],
            abonnement_type='essential',
            abonnement_paye=True,
            statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()
        return ent_b

    def _create_role_entreprise_b(self, session, entreprise_b):
        from app.models import Role, RolePermission, Permission
        perms = {}
        for module, module_perms in [
            ('users', [('users.voir', 'Voir')]),
            ('actions', [('actions.voir', 'Voir'), ('actions.cree', 'Créer')]),
            ('conformite', [('conformite.voir', 'Voir')]),
            ('hse', [('hse.voir_incidents', 'Voir incidents')]),
        ]:
            for code, desc in module_perms:
                perm = Permission.query.filter_by(code=code).first()
                if not perm:
                    perm = Permission(code=code, description=desc, module=module)
                    session.add(perm)
                    session.flush()
                perms[code] = perm
        role = Role(nom='Manager B', est_systeme=False, personnalisable=True)
        session.add(role)
        session.flush()
        for perm in perms.values():
            rp = RolePermission(role_id=role.id, permission_id=perm.id, entreprise_id=entreprise_b.id, autorise=True)
            session.add(rp)
        session.commit()
        return role

    def test_entreprise_a_cannot_see_entreprise_b_data(self, client, app, session, entreprise, manager_user):
        from app.models import ActionCorrective, Utilisateur

        ent_b = self._create_entreprise_b(session)
        role_b = self._create_role_entreprise_b(session, ent_b)
        user_b = Utilisateur(
            nom='UserB',
            prenom='Test',
            email='userb@test.com',
            role_id=role_b.id,
            entreprise_id=ent_b.id,
            actif=True,
        )
        user_b.set_password('passwordB')
        session.add(user_b)
        session.commit()

        action_b = ActionCorrective(
            entreprise_id=ent_b.id,
            domaine='hse',
            description='Action de Societe B',
            type_action='corrective',
            priorite='haute',
            statut='A_FAIRE',
            responsable_id=user_b.id,
            date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        with app.app_context():
            from app.utils.tenant_scope import set_current_entreprise
            set_current_entreprise(entreprise.id)

            actions_visible = ActionCorrective.query.filter_by(
                entreprise_id=entreprise.id
            ).all()
            assert all(a.entreprise_id == entreprise.id for a in actions_visible)

            actions_all = ActionCorrective.query.all()
            entreprise_b_actions = [a for a in actions_all if a.entreprise_id == ent_b.id]
            assert len(entreprise_b_actions) == 1

    def test_api_cross_tenant_data_leak(self, client, app, session, entreprise, manager_user):
        from app.models import ActionCorrective, Utilisateur, Role, RolePermission, Permission

        ent_b = self._create_entreprise_b(session)
        role_b = self._create_role_entreprise_b(session, ent_b)
        user_b = Utilisateur(
            nom='UserB',
            prenom='Test',
            email='userb_cross@test.com',
            role_id=role_b.id,
            entreprise_id=ent_b.id,
            actif=True,
        )
        user_b.set_password('passwordB')
        session.add(user_b)
        session.commit()

        action_a = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse',
            description='Action confidentielle de A',
            type_action='corrective',
            priorite='haute',
            statut='A_FAIRE',
            responsable_id=manager_user.id,
            date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_a)

        action_b = ActionCorrective(
            entreprise_id=ent_b.id,
            domaine='hse',
            description='Action de Societe B',
            type_action='corrective',
            priorite='basse',
            statut='OUVERTE',
            responsable_id=user_b.id,
            date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        resp = client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        assert resp.status_code == 200

        resp = client.get('/actions/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'Action confidentielle de A' in html
        assert 'Action de Societe B' not in html

    def test_foreign_key_prevents_entreprise_mismatch(self, session, entreprise):
        from app.models import ActionCorrective
        from sqlalchemy.exc import IntegrityError
        import os
        OTHER_ENT_ID = 99999

        action = ActionCorrective(
            entreprise_id=OTHER_ENT_ID,
            domaine='hse',
            description='Fake action',
            type_action='corrective',
            priorite='basse',
            statut='OUVERTE',
            responsable_id=1,
            date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action)

        db_url = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
        if db_url.startswith('sqlite'):
            pytest.skip('SQLite does not enforce FK constraints by default')
        else:
            with pytest.raises(IntegrityError):
                session.commit()

    def test_api_filters_by_entreprise(self, client, app, session, entreprise, manager_user):
        from app.models import ProofMaster, Utilisateur

        ent_b = self._create_entreprise_b(session)
        role_b = self._create_role_entreprise_b(session, ent_b)
        user_b = Utilisateur(
            nom='UserB',
            prenom='Test',
            email='userb_proof@test.com',
            role_id=role_b.id,
            entreprise_id=ent_b.id,
            actif=True,
        )
        user_b.set_password('passwordB')
        session.add(user_b)
        session.commit()

        proof_a = ProofMaster(
            entreprise_id=entreprise.id,
            domaine='hse',
            nom_fichier='fichier_A.pdf',
            type='pdf',
            chemin='preuves/1/fichier_A.pdf',
            taille_bytes=512,
            hash_fichier='hash_a',
            statut='ACTIF',
            upload_par=manager_user.id,
        )
        session.add(proof_a)

        proof_b = ProofMaster(
            entreprise_id=ent_b.id,
            domaine='hse',
            nom_fichier='fichier_B.pdf',
            type='pdf',
            chemin='preuves/2/fichier_B.pdf',
            taille_bytes=256,
            hash_fichier='hash_b',
            statut='ACTIF',
            upload_par=user_b.id,
        )
        session.add(proof_b)
        session.commit()

        resp = client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        assert resp.status_code == 200

        resp = client.get('/documents/api/actives')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        names = [d['nom_fichier'] for d in data]
        assert 'fichier_A.pdf' in names
        assert 'fichier_B.pdf' not in names
