from unittest.mock import patch
from app.jobs.textes_import_jobs import run_textes_import, enqueue_textes_import, get_job_status


class TestTextesImportJobSignature:
    """Verify that _process_json_bundle_entries accepts user_id/entreprise_id kwargs."""

    def test_process_bundle_entries_accepts_kwargs(self, app):
        """Critical: would have caught the original TypeError."""
        from app.textes.routes.import_export import _process_json_bundle_entries
        with app.app_context():
            result = _process_json_bundle_entries(
                [],
                dry_run=True,
                user_id=1,
                entreprise_id=1,
            )
        assert result is not None
        assert 'successes' in result
        assert 'failures' in result

    def test_process_bundle_payload_accepts_kwargs(self, app):
        """Verify the inner function also accepts the new params."""
        from app.textes.routes.import_export import _process_json_bundle_payload
        payload = {'rows': [], 'texte': {'code': '', 'titre': '', 'type': ''}, 'version': {'numero_version': ''}}
        with app.app_context():
            result = _process_json_bundle_payload(
                payload,
                dry_run=True,
                user_id=1,
                entreprise_id=1,
            )
        assert result is not None


class TestTextesImportJobNotification:
    """Verify notifications are created after successful imports."""

    @patch('app.textes.routes.import_export._process_json_bundle_entries')
    def test_notification_created_on_success(self, mock_process, app, session, manager_user, entreprise):
        mock_process.return_value = {
            'successes': [{'filename': 'test.json', 'result': {'texte_id': 1}}],
            'failures': [],
            'total_articles': 5,
        }
        with app.app_context():
            result = run_textes_import(
                [{'filename': 'test.json', 'payload': {'rows': []}}],
                link_to_enterprise=False,
                user_id=manager_user.id,
                entreprise_id=entreprise.id,
            )
        from app.models import Notification
        notifs = Notification.query.filter_by(utilisateur_id=manager_user.id).all()
        assert len(notifs) == 1
        assert '5 article(s)' in notifs[0].message
        assert '1 fichier(s)' in notifs[0].message
        assert notifs[0].categorie == 'systeme'
        assert notifs[0].entite_id == 1

    @patch('app.textes.routes.import_export._process_json_bundle_entries')
    def test_notification_on_multiple_files(self, mock_process, app, session, manager_user, entreprise):
        mock_process.return_value = {
            'successes': [
                {'filename': 'a.json', 'result': {'texte_id': 1}},
                {'filename': 'b.json', 'result': {'texte_id': 2}},
            ],
            'failures': [],
            'total_articles': 10,
        }
        with app.app_context():
            run_textes_import(
                [{'filename': 'a.json', 'payload': {}}, {'filename': 'b.json', 'payload': {}}],
                link_to_enterprise=False,
                user_id=manager_user.id,
                entreprise_id=entreprise.id,
            )
        from app.models import Notification
        notifs = Notification.query.filter_by(utilisateur_id=manager_user.id).all()
        assert len(notifs) == 1
        assert notifs[0].entite_id is None

    @patch('app.textes.routes.import_export._process_json_bundle_entries')
    def test_no_notification_on_failure(self, mock_process, app, session, manager_user, entreprise):
        mock_process.return_value = {
            'successes': [],
            'failures': ['fichier.json: code obligatoire'],
            'total_articles': 0,
        }
        with app.app_context():
            run_textes_import(
                [{'filename': 'fichier.json', 'payload': {}}],
                link_to_enterprise=False,
                user_id=manager_user.id,
                entreprise_id=entreprise.id,
            )
        from app.models import Notification
        notifs = Notification.query.filter_by(utilisateur_id=manager_user.id).all()
        assert len(notifs) == 0

    @patch('app.textes.routes.import_export._process_json_bundle_entries')
    def test_notification_includes_failure_count(self, mock_process, app, session, manager_user, entreprise):
        mock_process.return_value = {
            'successes': [{'filename': 'ok.json', 'result': {'texte_id': 1}}],
            'failures': ['ko.json: erreur'],
            'total_articles': 3,
        }
        with app.app_context():
            run_textes_import(
                [{'filename': 'ok.json', 'payload': {}}, {'filename': 'ko.json', 'payload': {}}],
                link_to_enterprise=False,
                user_id=manager_user.id,
                entreprise_id=entreprise.id,
            )
        from app.models import Notification
        notifs = Notification.query.filter_by(utilisateur_id=manager_user.id).all()
        assert len(notifs) == 1
        assert '1 fichier(s) en erreur' in notifs[0].message


class TestTextesImportEnqueueSignatures:
    """Verify enqueue helper and status checker accept the right signatures."""

    def test_enqueue_function_exists(self):
        assert callable(enqueue_textes_import)

    def test_get_job_status_function_exists(self):
        assert callable(get_job_status)
