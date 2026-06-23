import pytest
from datetime import date


class TestAutoDiscovery:
    """Vérifie que _discover_scoped_models découvre tous les modèles attendus."""

    def test_all_base_model_subclasses_discovered(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models.base import BaseModel
        from app import db

        scoped = _discover_scoped_models()
        scoped_names = {m.__name__ for m in scoped}

        for mapper in db.Model.registry.mappers:
            model = mapper.class_
            if model is BaseModel:
                continue
            if issubclass(model, BaseModel):
                assert model.__name__ in scoped_names, \
                    f"{model.__name__} hérite de BaseModel mais n'est pas scopé"

    def test_entreprise_secteur_excluded(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models import EntrepriseSecteur

        scoped = _discover_scoped_models()
        assert EntrepriseSecteur not in scoped

    def test_role_permission_excluded(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models import RolePermission

        scoped = _discover_scoped_models()
        assert RolePermission not in scoped

    def test_ticket_excluded(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models import Ticket

        scoped = _discover_scoped_models()
        assert Ticket not in scoped

    def test_utilisateur_included(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models import Utilisateur

        scoped = _discover_scoped_models()
        assert Utilisateur in scoped

    def test_historique_paiement_included(self, app):
        from app.utils.tenant_scope import _discover_scoped_models
        from app.models import HistoriquePaiement

        scoped = _discover_scoped_models()
        assert HistoriquePaiement in scoped

    def test_at_least_60_models(self, app):
        from app.utils.tenant_scope import _discover_scoped_models

        scoped = _discover_scoped_models()
        assert len(scoped) >= 60


class TestAutoScoping:
    """Vérifie que le scope automatique filtre correctement les requêtes."""

    def test_bare_query_filters_by_entreprise(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import ActionCorrective

        set_current_entreprise(entreprise.id)

        action = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse', description='Test scope',
            type_action='corrective', priorite='haute',
            statut='A_FAIRE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action)
        session.commit()

        results = ActionCorrective.query.all()
        assert len(results) == 1
        assert results[0].id == action.id

    def test_cross_entreprise_isolation(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import ActionCorrective, Entreprise

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_a = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse', description='Action A',
            type_action='corrective', priorite='haute',
            statut='A_FAIRE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_a)
        action_b = ActionCorrective(
            entreprise_id=ent_b.id,
            domaine='qualite', description='Action B',
            type_action='corrective', priorite='basse',
            statut='OUVERTE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(entreprise.id)
        results = ActionCorrective.query.all()
        assert len(results) == 1
        assert results[0].description == 'Action A'

        set_current_entreprise(ent_b.id)
        results = ActionCorrective.query.all()
        assert len(results) == 1
        assert results[0].description == 'Action B'

    def test_system_admin_bypass(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import ActionCorrective, Entreprise

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_a = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse', description='Action A',
            type_action='corrective', priorite='haute',
            statut='A_FAIRE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_a)
        action_b = ActionCorrective(
            entreprise_id=ent_b.id,
            domaine='qualite', description='Action B',
            type_action='corrective', priorite='basse',
            statut='OUVERTE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(entreprise.id, is_system_admin=True)
        results = ActionCorrective.query.all()
        assert len(results) == 2

    def test_eid_none_no_filter(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise, clear_current_entreprise
        from app.models import ActionCorrective

        set_current_entreprise(entreprise.id)
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse', description='Test',
            type_action='corrective', priorite='haute',
            statut='A_FAIRE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action)
        session.commit()

        clear_current_entreprise()
        results = ActionCorrective.query.all()
        assert len(results) == 1

    def test_representative_models_filtered(self, app, session, entreprise):
        """Test sur un échantillon de modèles variés pour valider le scoping."""
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import (
            Entreprise, ActionCorrective, NonConformite,
            Fournisseur, Dossier,
        )

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse', 'qualite'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        samples = [
            (ActionCorrective, ActionCorrective(entreprise_id=ent_b.id, domaine='hse',
                description='Test', type_action='corrective', priorite='haute',
                statut='A_FAIRE', date_echeance=date.today(), est_recurrente=False)),
            (NonConformite, NonConformite(entreprise_id=ent_b.id, description='NC B',
                statut='OUVERTE', source='interne', domaine='hse')),
            (Fournisseur, Fournisseur(entreprise_id=ent_b.id, nom='Fournisseur B')),
            (Dossier, Dossier(entreprise_id=ent_b.id, nom='Dossier B')),
        ]

        for model_cls, obj in samples:
            session.add(obj)
        session.commit()

        set_current_entreprise(entreprise.id)
        for model_cls, obj in samples:
            results = model_cls.query.all()
            ids_b = [r.id for r in results if r.entreprise_id == ent_b.id]
            assert len(ids_b) == 0, \
                f"{model_cls.__name__}: trouvé enregistrement de B (id={obj.id})"

    def test_query_with_join_still_scoped(self, app, session, entreprise):
        """Vérifie que les JOINs restent scopés."""
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import ActionCorrective, Entreprise
        from sqlalchemy import select

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_a = ActionCorrective(
            entreprise_id=entreprise.id, domaine='hse',
            description='Action A', type_action='corrective',
            priorite='haute', statut='A_FAIRE',
            date_echeance=date.today(), est_recurrente=False,
        )
        session.add(action_a)
        action_b = ActionCorrective(
            entreprise_id=ent_b.id, domaine='qualite',
            description='Action B', type_action='corrective',
            priorite='basse', statut='OUVERTE',
            date_echeance=date.today(), est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(entreprise.id)

        stmt = select(ActionCorrective).join(Entreprise, ActionCorrective.entreprise_id == Entreprise.id)
        results = session.execute(stmt).scalars().all()
        assert len(results) == 1
        assert results[0].description == 'Action A'

    def test_session_execute_scoped(self, app, session, entreprise):
        """Vérifie que session.execute(select(Model)) est aussi scopé."""
        from app.utils.tenant_scope import set_current_entreprise
        from app.models import ActionCorrective, Entreprise
        from sqlalchemy import select

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_a = ActionCorrective(
            entreprise_id=entreprise.id, domaine='hse',
            description='Action A', type_action='corrective',
            priorite='haute', statut='A_FAIRE',
            date_echeance=date.today(), est_recurrente=False,
        )
        session.add(action_a)
        action_b = ActionCorrective(
            entreprise_id=ent_b.id, domaine='qualite',
            description='Action B', type_action='corrective',
            priorite='basse', statut='OUVERTE',
            date_echeance=date.today(), est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(entreprise.id)
        results = session.execute(select(ActionCorrective)).scalars().all()
        assert len(results) == 1
        assert results[0].description == 'Action A'


class TestTenantGetOr404:

    def test_returns_own_entreprise_record(self, app, session, entreprise, action):
        from app.utils.tenant_scope import set_current_entreprise, tenant_get_or_404
        from app.models import ActionCorrective

        set_current_entreprise(entreprise.id)
        obj = tenant_get_or_404(ActionCorrective, action.id)
        assert obj.id == action.id

    def test_404_for_other_entreprise_record(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise, tenant_get_or_404
        from app.models import ActionCorrective, Entreprise
        import pytest

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_b = ActionCorrective(
            entreprise_id=ent_b.id, domaine='hse', description='Action B',
            type_action='corrective', priorite='basse',
            statut='OUVERTE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(entreprise.id)
        with pytest.raises(Exception):
            tenant_get_or_404(ActionCorrective, action_b.id)

    def test_system_admin_can_access_any(self, app, session, entreprise):
        from app.utils.tenant_scope import set_current_entreprise, tenant_get_or_404
        from app.models import ActionCorrective, Entreprise

        ent_b = Entreprise(
            nom='Societe B', taille='PME', pays='Maroc',
            modules_actifs=['hse'], abonnement_type='essential',
            abonnement_paye=True, statut='active',
            date_inscription=date.today(),
        )
        session.add(ent_b)
        session.commit()

        action_b = ActionCorrective(
            entreprise_id=ent_b.id, domaine='hse', description='Action B',
            type_action='corrective', priorite='basse',
            statut='OUVERTE', date_echeance=date.today(),
            est_recurrente=False,
        )
        session.add(action_b)
        session.commit()

        set_current_entreprise(None, is_system_admin=True)
        obj = tenant_get_or_404(ActionCorrective, action_b.id)
        assert obj.id == action_b.id


class TestScopedModelsList:

    def test_scoped_models_initialized(self, app):
        import app.utils.tenant_scope as ts
        assert len(ts.SCOPED_MODELS) > 7

    def test_scoped_models_include_base_model_subclasses(self, app):
        import app.utils.tenant_scope as ts
        from app.models.base import BaseModel
        from app import db

        scoped_names = {m.__name__ for m in ts.SCOPED_MODELS}

        for mapper in db.Model.registry.mappers:
            model = mapper.class_
            if model is BaseModel:
                continue
            if issubclass(model, BaseModel):
                assert model.__name__ in scoped_names, \
                    f"{model.__name__} (BaseModel) absent de SCOPED_MODELS"

    def test_excluded_models_not_scoped(self, app):
        import app.utils.tenant_scope as ts

        scoped_names = {m.__name__ for m in ts.SCOPED_MODELS}
        assert 'EntrepriseSecteur' not in scoped_names
        assert 'RolePermission' not in scoped_names
        assert 'Ticket' not in scoped_names

    def test_utilisateur_in_scoped(self, app):
        import app.utils.tenant_scope as ts
        from app.models import Utilisateur

        assert Utilisateur in ts.SCOPED_MODELS
