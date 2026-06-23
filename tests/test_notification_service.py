"""Tests for NotificationService and that all notifications go through it."""
import json
import pytest
from app import db
from app.models.systeme import Notification, NotificationPreference
from app.services.notification_service import NotificationService
from app.utils.notifications import create_notification


class TestNotificationService:
    def test_notify_creates_in_app_notification(self, session, manager_user):
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='Test notification',
            skip_module_check=True,
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif is not None
        assert notif.message == 'Test notification'
        assert notif.categorie == 'general'
        assert notif.lu is False

    def test_notify_respects_app_disabled(self, session, manager_user):
        pref = NotificationPreference(
            utilisateur_id=manager_user.id,
            categorie='general',
            app_enabled=False,
            email_enabled=False,
        )
        session.add(pref)
        session.commit()

        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='Should not appear',
            skip_module_check=True,
        )
        count = Notification.query.filter_by(utilisateur_id=manager_user.id).count()
        assert count == 0

    def test_notify_without_preferences_defaults_for_high_urgency(self, session, manager_user):
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='High urgency',
            urgence='haute',
            skip_module_check=True,
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif is not None

    def test_notify_suppress_send(self, app, session, manager_user):
        app.config['MAIL_SUPPRESS_SEND'] = True
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='Mail suppressed',
            skip_module_check=True,
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif is not None
        app.config['MAIL_SUPPRESS_SEND'] = False

    def test_notify_unknown_user_returns_false(self, session):
        result = NotificationService.notify(
            utilisateur_id=99999,
            category='general',
            message='No user',
            skip_module_check=True,
        )
        assert result is False

    def test_notify_system_admins(self, session, admin_user):
        NotificationService.notify_system_admins(
            category='technique',
            message='System alert test',
        )
        notif = Notification.query.filter_by(utilisateur_id=admin_user.id).first()
        assert notif is not None
        assert 'System alert test' in notif.message

    def test_notify_managers(self, session, manager_user, entreprise):
        NotificationService.notify_managers(
            entreprise_id=entreprise.id,
            category='general',
            message='Manager alert',
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif is not None


class TestCreateNotificationWrapper:
    def test_create_notification_delegates_to_service(self, session, manager_user):
        create_notification(
            user_id=manager_user.id,
            message='Via wrapper',
            type='info',
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif is not None
        assert notif.message == 'Via wrapper'

    def test_create_notification_maps_type_to_category(self, session, manager_user):
        create_notification(
            user_id=manager_user.id,
            message='Incident test',
            type='incident',
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif.categorie == 'hse'
        assert notif.urgence == 'haute'

    def test_create_notification_unknown_type_defaults_general(self, session, manager_user):
        create_notification(
            user_id=manager_user.id,
            message='Unknown type',
            type='unknown_type_xyz',
        )
        notif = Notification.query.filter_by(utilisateur_id=manager_user.id).first()
        assert notif.categorie == 'general'
        assert notif.urgence == 'normale'


class TestAdminNotificationRoute:
    def test_admin_send_creates_notification(self, client, admin_user, manager_user):
        client.post('/users/login', data={
            'email': admin_user.email,
            'password': 'admin123',
        }, follow_redirects=True)
        resp = client.post('/admin/notifications/send', data={
            'type': 'info',
            'message': 'Admin test notification',
            'utilisateur_id': str(manager_user.id),
        }, follow_redirects=True)
        assert resp.status_code == 200
        notif = Notification.query.filter_by(
            utilisateur_id=manager_user.id,
            message='Admin test notification',
        ).first()
        assert notif is not None

    def test_admin_send_broadcast_to_all(self, client, admin_user, manager_user, session):
        other = manager_user.__class__(
            nom='Other',
            prenom='User',
            email='other@test.com',
            role_id=manager_user.role_id,
            entreprise_id=manager_user.entreprise_id,
            actif=True,
        )
        other.set_password('test123')
        session.add(other)
        session.commit()

        client.post('/users/login', data={
            'email': admin_user.email,
            'password': 'admin123',
        }, follow_redirects=True)
        resp = client.post('/admin/notifications/send', data={
            'type': 'info',
            'message': 'Broadcast test',
        }, follow_redirects=True)
        assert resp.status_code == 200
        count = Notification.query.filter_by(message='Broadcast test').count()
        assert count >= 2

    def test_admin_send_without_message_fails(self, client, admin_user):
        client.post('/users/login', data={
            'email': admin_user.email,
            'password': 'admin123',
        }, follow_redirects=True)
        resp = client.post('/admin/notifications/send', data={
            'type': 'info',
            'message': '',
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestNotificationPreferenceRoute:
    def test_preferences_page_renders(self, login_client):
        resp = login_client.get('/users/notifications/preferences')
        assert resp.status_code == 200

    def test_update_preferences(self, login_client, session):
        resp = login_client.post('/users/notifications/preferences', data={
            'app_general': 'on',
            'email_general': 'off',
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestDashboardAlertsAPI:
    def test_dashboard_alerts_returns_notifications(self, client, manager_user):
        from app.utils.notifications import create_notification
        create_notification(manager_user.id, 'Dashboard test', type='info')
        db.session.commit()

        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/api/dashboard/alerts')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert 'notifications' in data
        assert len(data['notifications']) >= 1
        assert any('Dashboard test' in n['message'] for n in data['notifications'])

    def test_dashboard_alerts_filters_technique_for_non_admin(self, client, manager_user, admin_user):
        from app.services.notification_service import NotificationService
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='technique',
            message='Technique test',
            skip_module_check=True,
        )
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='General test',
            skip_module_check=True,
        )

        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/api/dashboard/alerts')
        data = resp.get_json()
        messages = [n['message'] for n in data['notifications']]
        assert 'General test' in messages
        assert 'Technique test' not in messages

    def test_dashboard_alerts_shows_technique_for_admin(self, client, admin_user):
        from app.services.notification_service import NotificationService
        NotificationService.notify(
            utilisateur_id=admin_user.id,
            category='technique',
            message='Admin technique',
            skip_module_check=True,
        )

        client.post('/users/login', data={
            'email': admin_user.email,
            'password': 'admin123',
        }, follow_redirects=True)
        resp = client.get('/api/dashboard/alerts')
        data = resp.get_json()
        messages = [n['message'] for n in data['notifications']]
        assert 'Admin technique' in messages

    def test_dashboard_alerts_aggregated_counts(self, client, admin_user, session, entreprise):
        from app.models import ActionCorrective
        from datetime import date, timedelta
        action = ActionCorrective(
            entreprise_id=entreprise.id,
            domaine='hse',
            description='Overdue test action',
            type_action='corrective',
            priorite='haute',
            statut='A_FAIRE',
            responsable_id=admin_user.id,
            date_echeance=date.today() - timedelta(days=5),
        )
        session.add(action)
        session.commit()

        client.post('/users/login', data={
            'email': admin_user.email,
            'password': 'admin123',
        }, follow_redirects=True)
        resp = client.get('/api/dashboard/alerts')
        data = resp.get_json()
        assert data['overdue_actions'] >= 1

    def test_api_notifications_filters_technique_for_regular_user(self, client, manager_user):
        from app.services.notification_service import NotificationService
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='technique',
            message='Hidden tech',
            skip_module_check=True,
        )
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='general',
            message='Visible',
            skip_module_check=True,
        )

        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/api/notifications')
        data = resp.get_json()
        messages = [n['message'] for n in data]
        assert 'Visible' in messages
        assert 'Hidden tech' not in messages

    def test_notifications_page_renders(self, client, manager_user):
        from app.utils.notifications import create_notification
        create_notification(manager_user.id, 'Page test', type='info')

        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/notifications')
        assert resp.status_code == 200
        assert b'Page test' in resp.data

    def test_notifications_page_accessible_by_all(self, client, manager_user):
        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/notifications')
        assert resp.status_code == 200

    def test_unread_count_filters_technique(self, client, manager_user):
        from app.services.notification_service import NotificationService
        NotificationService.notify(
            utilisateur_id=manager_user.id,
            category='technique',
            message='Hidden unread',
            skip_module_check=True,
        )
        client.post('/users/login', data={
            'email': manager_user.email,
            'password': 'manager123',
        }, follow_redirects=True)
        resp = client.get('/api/notifications/unread-count')
        data = resp.get_json()
        assert data['unread'] == 0


class TestNoDirectNotificationInstantiation:
    """Guard against regressions: no new direct Notification() calls outside service."""

    ALLOWED_FILES = {
        'app/services/notification_service.py',
        'app/models/systeme.py',
        'app/utils/notifications.py',
    }

    def test_no_direct_notification_instantiation_outside_service(self):
        import os
        import ast
        root = os.path.join(os.path.dirname(__file__), '..', 'app')
        violations = []
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith('.py'):
                    continue
                fpath = os.path.join(dirpath, fn)
                rel = os.path.relpath(fpath, os.path.join(root, '..'))
                if rel in self.ALLOWED_FILES:
                    continue
                with open(fpath) as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id == 'Notification':
                            violations.append(f'{rel}:{node.lineno}: Notification(...)')
        assert not violations, (
            f"Direct Notification() instantiation found outside allowed files. "
            f"Use create_notification() or NotificationService.notify() instead.\n"
            + '\n'.join(violations)
        )
