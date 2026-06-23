import os
from flask import render_template, request, redirect, url_for, flash, abort, jsonify, current_app
from flask_login import login_required, current_user
from app.admin import admin
from app import db, mail
from app.models import (
    Utilisateur, JournalSecurite, Notification,
    SubscriptionPlan, Entreprise,
)
from app.services.backup_service import BackupService
from app.services.subscription_service import apply_subscription_update
from app.utils.permission_catalog import iter_permission_rows, PERMISSION_CATALOG
from app.utils.subscriptions import _seed_default_plans
from functools import wraps
from flask_mail import Message
from datetime import date, timedelta, datetime
import os, shutil


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403)
        if not current_user.role or not current_user.role.est_systeme:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route('/securite')
@login_required
@admin_required
def securite():
    type_action = request.args.get('type_action')
    query = JournalSecurite.query
    if type_action:
        query = query.filter_by(type_action=type_action)
    logs = query.order_by(JournalSecurite.date_action.desc()).all()
    types = [t[0] for t in db.session.query(JournalSecurite.type_action).distinct().all()]
    utilisateurs = {u.id: u for u in Utilisateur.query.all()}
    return render_template('admin/securite.html', logs=logs, types=types, utilisateurs=utilisateurs)


@admin.route('/securite/<int:incident_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_incident(incident_id):
    try:
        incident = db.session.get(JournalSecurite, incident_id)
        if not incident:
            return jsonify({'success': False, 'error': 'Introuvable'}), 404
        incident.resolu = True
        incident.resolved_at = datetime.utcnow()
        incident.resolved_by = current_user.id
        db.session.commit()
        return jsonify({'success': True, 'resolved_at': incident.resolved_at.isoformat()})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Erreur serveur'}), 500


@admin.route('/notifications')
@login_required
@admin_required
def notifications():
    """
    Vue d'administration des notifications.
    
    Supporte les filtres GET :
      - type     : type de notification (incident, overdue, info…)
      - statut   : 'lu' | 'non_lu'
      - user_id  : ID utilisateur
      - q        : recherche dans le message
    """
    q_type   = request.args.get('type', '').strip()
    q_statut = request.args.get('statut', '').strip()
    q_user   = request.args.get('user_id', '').strip()
    q_search = request.args.get('q', '').strip()

    query = Notification.query

    if q_type:
        query = query.filter(Notification.type == q_type)
    if q_statut == 'lu':
        query = query.filter(Notification.lu == True)
    elif q_statut == 'non_lu':
        query = query.filter(Notification.lu == False)
    if q_user:
        query = query.filter(Notification.utilisateur_id == int(q_user))
    if q_search:
        query = query.filter(Notification.message.ilike(f'%{q_search}%'))

    notifs = query.order_by(Notification.date_envoi.desc()).all()
    utilisateurs = Utilisateur.query.order_by(Utilisateur.nom).all()
    users_dict = {u.id: u for u in utilisateurs}

    return render_template(
        'admin/notifications.html',
        notifications=notifs,
        utilisateurs=utilisateurs,
        users_dict=users_dict,
    )


@admin.route('/notifications/send', methods=['POST'])
@login_required
@admin_required
def notification_send():
    from app.utils.notifications import create_notification
    type_notif = request.form.get('type', 'info')
    message = request.form.get('message', '').strip()
    utilisateur_id = request.form.get('utilisateur_id')
    if not message:
        flash('Le message est requis.', 'danger')
        return redirect(url_for('admin.notifications'))
    if utilisateur_id:
        create_notification(int(utilisateur_id), message, type=type_notif)
    else:
        for u in Utilisateur.query.all():
            create_notification(u.id, message, type=type_notif)
    flash('Notification(s) envoyée(s).', 'success')
    return redirect(url_for('admin.notifications'))


@admin.route('/notifications/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def notification_delete(id):
    notif = db.session.get(Notification, id)
    if notif:
        db.session.delete(notif)
        db.session.commit()
        flash('Notification supprimée.', 'success')
    else:
        flash('Notification introuvable.', 'danger')
    return redirect(url_for('admin.notifications'))


@admin.route('/notifications/delete-all', methods=['POST'])
@login_required
@admin_required
def notifications_delete_all():
    try:
        Notification.query.delete()
        db.session.commit()
        flash('Toutes les notifications ont été supprimées.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    return redirect(url_for('admin.notifications'))


@admin.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@admin_required
def notifications_mark_all_read():
    try:
        Notification.query.filter_by(lu=False).update({'lu': True})
        db.session.commit()
        flash('Toutes les notifications ont été marquées comme lues.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur : {str(e)}', 'danger')
    return redirect(url_for('admin.notifications'))


@admin.route('/mail-test')
@login_required
@admin_required
def mail_test():
    """Page de diagnostic de la configuration mail."""
    config = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER', ''),
        'MAIL_PORT': current_app.config.get('MAIL_PORT', ''),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS', ''),
        'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL', ''),
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER', ''),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME', ''),
        'MAIL_SUPPRESS_SEND': current_app.config.get('MAIL_SUPPRESS_SEND', ''),
        'REDIS_URL': current_app.config.get('REDIS_URL', ''),
    }
    mismatch = False
    if config['MAIL_DEFAULT_SENDER'] and config['MAIL_USERNAME']:
        if config['MAIL_DEFAULT_SENDER'] != config['MAIL_USERNAME']:
            mismatch = True
    return render_template('admin/mail_test.html', config=config, mismatch=mismatch)


@admin.route('/mail-test/send', methods=['POST'])
@login_required
@admin_required
def mail_test_send():
    """Envoie un email de test pour vérifier la configuration."""
    try:
        from flask_mail import Message
        msg = Message(
            subject="Test QMS — Configuration email OK",
            recipients=[current_user.email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        )
        msg.body = "Ceci est un email de test depuis QMS Platform. Si vous le recevez, la configuration email est fonctionnelle."
        msg.html = """
        <div style="font-family:sans-serif;padding:20px;background:#f8f9fa;">
            <h2 style="color:#e63946;">Test QMS Platform</h2>
            <p>Ceci est un email de test.</p>
            <p style="color:#28a745;font-weight:bold;">✓ Configuration email fonctionnelle</p>
            <hr>
            <p style="font-size:0.8rem;color:#666;">Envoyé depuis QMS Platform</p>
        </div>
        """
        mail.send(msg)
        flash(f"Email de test envoyé avec succès à {current_user.email}.", 'success')
    except Exception as e:
        flash(f"Échec de l'envoi de l'email de test : {str(e)}", 'danger')
    return redirect(url_for('admin.mail_test'))


@admin.route('/plans')
@login_required
@admin_required
def plans():
    plans_list = SubscriptionPlan.query.order_by(SubscriptionPlan.price_mad).all()
    all_feature_keys = []
    seen = set()
    for p in plans_list:
        if p.features:
            for k in p.features:
                if k not in seen:
                    all_feature_keys.append(k)
                    seen.add(k)
    return render_template('admin/plans.html', plans=plans_list,
                           all_feature_keys=all_feature_keys)


@admin.route('/plans/seed', methods=['POST'])
@login_required
@admin_required
def plans_seed():
    _seed_default_plans()
    flash('Plans d\'abonnement par défaut créés.', 'success')
    return redirect(url_for('admin.plans'))


@admin.route('/plans/entreprises')
@login_required
@admin_required
def plans_entreprises():
    return redirect(url_for('admin.entreprises'))


@admin.route('/plans/entreprises/<int:eid>/update', methods=['POST'])
@login_required
@admin_required
def plans_entreprises_update(eid):
    entreprise = db.session.get(Entreprise, eid)
    if not entreprise:
        abort(404)
    payload = request.get_json() or {}
    try:
        apply_subscription_update(entreprise, payload)
        db.session.commit()
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@admin.route('/backups')
@login_required
@admin_required
def backups():
    service = BackupService()
    backups_list = service.list_backups()
    return render_template('admin/backups.html', backups=backups_list)


@admin.route('/backups/create', methods=['POST'])
@login_required
@admin_required
def backup_create():
    service = BackupService()
    try:
        filename = service.create_backup()
        flash(f'Sauvegarde créée : {filename}', 'success')
    except Exception as e:
        flash(f'Erreur lors de la création de la sauvegarde : {e}', 'danger')
    return redirect(url_for('admin.backups'))


@admin.route('/backups/<filename>/restore', methods=['POST'])
@login_required
@admin_required
def backup_restore(filename):
    service = BackupService()
    try:
        service.restore_backup(filename)
        flash(f'Sauvegarde restaurée : {filename}', 'success')
    except Exception as e:
        flash(f'Erreur lors de la restauration : {e}', 'danger')
    return redirect(url_for('admin.backups'))


@admin.route('/backups/<filename>/delete', methods=['POST'])
@login_required
@admin_required
def backup_delete(filename):
    service = BackupService()
    if service.delete_backup(filename):
        flash(f'Sauvegarde supprimée : {filename}', 'success')
    else:
        flash(f'Fichier introuvable : {filename}', 'danger')
    return redirect(url_for('admin.backups'))


def _check_service(name, ok, detail='', hint=''):
    return {'name': name, 'ok': ok, 'detail': detail, 'hint': hint}


@admin.route('/services')
@login_required
@admin_required
def services():
    checks = []

    # ── PostgreSQL ──
    try:
        db.session.execute(db.text('SELECT 1'))
        checks.append(_check_service('PostgreSQL', True, 'Connexion OK'))
    except Exception as e:
        checks.append(_check_service('PostgreSQL', False, str(e), 'Vérifiez que le conteneur db est running'))

    # ── Redis ──
    try:
        from redis import Redis
        url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        r = Redis.from_url(url)
        r.ping()
        info = r.info()
        used_mem = info.get('used_memory_human', '?')
        uptime = info.get('uptime_in_days', 0)
        checks.append(_check_service('Redis', True, f'Connecté, uptime {uptime}j, mémoire {used_mem}'))
        r.close()
    except Exception as e:
        checks.append(_check_service('Redis', False, str(e), 'Vérifiez que le conteneur redis est running'))

    # ── RQ Worker & Queues ──
    queues_info = {}
    try:
        from redis import Redis as R
        from rq import Queue, Worker
        from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
        conn = R.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
        workers = Worker.all(connection=conn)
        for qname in ['high', 'default', 'low']:
            try:
                q = Queue(qname, connection=conn)
                started = len(StartedJobRegistry(qname, connection=conn))
                finished = len(FinishedJobRegistry(qname, connection=conn))
                failed = len(FailedJobRegistry(qname, connection=conn))
                queues_info[qname] = {'queued': q.count, 'started': started, 'finished': finished, 'failed': failed}
            except Exception:
                queues_info[qname] = None
        if workers:
            w = workers[0]
            queue_names = ', '.join(q.name for q in w.queues)
            detail = f'{len(workers)} worker(s) — files: {queue_names}'
            for qn, qi in queues_info.items():
                if qi:
                    detail += f' | {qn}: {qi["queued"]} en attente, {qi["failed"]} échoués'
            checks.append(_check_service('Worker RQ', True, detail))
        else:
            checks.append(_check_service('Worker RQ', False, 'Aucun worker trouvé', 'Lancez le worker: docker start qms_worker'))
    except Exception as e:
        checks.append(_check_service('Worker RQ', False, str(e), 'Redis injoignable ou RQ non installé'))

    # ── MinIO (S3) ──
    try:
        import boto3
        from botocore.config import Config as BotoConfig
        endpoint = current_app.config.get('MINIO_ENDPOINT', 'http://minio:9000')
        access = current_app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
        secret = current_app.config.get('MINIO_SECRET_KEY', 'minioadmin')
        bucket = current_app.config.get('MINIO_BUCKET', 'qms-platform')
        client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
            config=BotoConfig(connect_timeout=3, retries={'max_attempts': 1}),
        )
        buckets = client.list_buckets()
        bucket_names = [b['Name'] for b in buckets['Buckets']]
        exists = bucket in bucket_names
        checks.append(_check_service('MinIO (S3)',
            exists,
            f'Buckets: {", ".join(bucket_names)}' if bucket_names else 'Aucun bucket',
            f'Bucket "{bucket}" introuvable' if not exists else ''))
    except Exception as e:
        checks.append(_check_service('MinIO (S3)', False, str(e), 'Vérifiez que le conteneur minio est running'))

    # ── Mail (SMTP) ──
    mail_server = current_app.config.get('MAIL_SERVER', '')
    mail_port = current_app.config.get('MAIL_PORT', '')
    mail_user = current_app.config.get('MAIL_USERNAME', '')
    mail_from = current_app.config.get('MAIL_DEFAULT_SENDER', '')
    mail_suppress = current_app.config.get('MAIL_SUPPRESS_SEND', False)
    if mail_suppress:
        checks.append(_check_service('SMTP', False, 'MAIL_SUPPRESS_SEND est activé — les emails ne sont pas envoyés',
            'Désactivez MAIL_SUPPRESS_SEND dans .env'))
    elif not mail_server:
        checks.append(_check_service('SMTP', False, 'MAIL_SERVER non configuré', 'Configurez le SMTP dans .env'))
    else:
        mismatch = mail_from != mail_user and mail_user
        hint = 'MAIL_DEFAULT_SENDER ≠ MAIL_USERNAME — certains SMTP rejettent l\'envoi' if mismatch else ''
        checks.append(_check_service('SMTP', True,
            f'{mail_server}:{mail_port} — expéditeur: {mail_from}', hint))

    # ── Disque (stockage des uploads) ──
    try:
        upload_path = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(current_app.root_path), 'uploads'))
        os.makedirs(upload_path, exist_ok=True)
        usage = shutil.disk_usage(upload_path)
        total_gb = usage.total / (1024**3)
        free_gb = usage.free / (1024**3)
        pct = usage.used / usage.total * 100
        warn = 'Espace disque faible (< 5 Go)' if free_gb < 5 else ''
        checks.append(_check_service('Stockage (Disque)',
            free_gb > 1,
            f'{free_gb:.1f} Go libre / {total_gb:.1f} Go total ({pct:.0f}% utilisé)',
            warn))
    except Exception as e:
        checks.append(_check_service('Stockage (Disque)', False, str(e), ''))

    # ── Modules / Plugins ──
    try:
        from app.core import plugin_manager
        pm_stats = plugin_manager.get_stats()
        all_mods = plugin_manager.get_all_manifests()
        cat_count = len(pm_stats.get('categories', {}))
        checks.append(_check_service('Modules (Plugins)',
            True,
            f'{pm_stats.get("total_modules", 0)} modules · {cat_count} catégories · {pm_stats.get("total_permissions", 0)} permissions'))
    except Exception as e:
        checks.append(_check_service('Modules (Plugins)', False, str(e)))

    # ── Connexions BDD (Pool) ──
    try:
        pool = db.engine.pool
        pool_size = pool.size()
        checked_out = pool.checkedout()
        overflow = pool.overflow()
        detail = f'{checked_out} actives · {pool_size - checked_out} disponibles · overflow: {overflow}'
        checks.append(_check_service('Pool BDD', True, detail))
    except Exception as e:
        checks.append(_check_service('Pool BDD', False, str(e)))

    # ── Utilisateurs actifs ──
    try:
        from app.models import Utilisateur
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        recent = Utilisateur.query.filter(Utilisateur.dernier_acces >= cutoff, Utilisateur.actif == True).count()
        total = Utilisateur.query.filter(Utilisateur.actif == True).count()
        checks.append(_check_service('Utilisateurs', True,
            f'{total} actifs · {recent} connectés dans les 15 min'))
    except Exception as e:
        checks.append(_check_service('Utilisateurs', True, str(e)))

    # ── Environnement ──
    try:
        env = current_app.config.get('FLASK_ENV', 'production')
        debug = current_app.config.get('DEBUG', False)
        routes_count = len(list(current_app.url_map.iter_rules()))
        import platform as _pf
        hostname = _pf.node()
        server_time = datetime.utcnow().strftime('%H:%M UTC')
        detail = f'{env} · debug: {"oui" if debug else "non"} · {routes_count} routes · {hostname} · {server_time}'
        checks.append(_check_service('Environnement', True, detail))
    except Exception as e:
        checks.append(_check_service('Environnement', True, str(e)))

    # ── Health API (/health) ──
    db_ok = any(c['name'] == 'PostgreSQL' and c['ok'] for c in checks)
    redis_ok = any(c['name'] == 'Redis' and c['ok'] for c in checks)
    try:
        import platform as pf
        py_ver = pf.python_version()
    except Exception:
        py_ver = '?'
    health_api = {
        'status': 'ok' if (db_ok and redis_ok) else 'degraded',
        'database': 'ok' if db_ok else 'error',
        'redis': 'ok' if redis_ok else 'error',
        'python': py_ver,
        'flask': '2.3.3',
        'mail': {k: current_app.config.get(k, '') for k in ('MAIL_SERVER', 'MAIL_PORT', 'MAIL_DEFAULT_SENDER', 'MAIL_SUPPRESS_SEND')},
    }
    health_detail = f'BDD {"✓" if db_ok else "✗"} · Redis {"✓" if redis_ok else "✗"} · Python {py_ver}'
    checks.append(_check_service('Health API (/health)', db_ok and redis_ok, health_detail,
        'Accès: GET http://localhost:5006/health' if (db_ok and redis_ok) else ''))

    # ── CPU / RAM ──
    try:
        import psutil
        cpu_pct = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        ram_used_gb = mem.used / (1024**3)
        ram_total_gb = mem.total / (1024**3)
        checks.append(_check_service('CPU', cpu_pct < 90,
            f'{cpu_pct}% utilisé'))
        checks.append(_check_service('RAM', mem.percent < 90,
            f'{ram_used_gb:.1f} Go / {ram_total_gb:.1f} Go ({mem.percent}% utilisé)'))
    except ImportError:
        try:
            with open('/proc/meminfo') as f:
                meminfo = f.read()
            total_kb = int([l for l in meminfo.split('\n') if 'MemTotal' in l][0].split()[1])
            avail_kb = int([l for l in meminfo.split('\n') if 'MemAvailable' in l][0].split()[1])
            used_kb = total_kb - avail_kb
            ram_used_gb = used_kb / (1024**2)
            ram_total_gb = total_kb / (1024**2)
            checks.append(_check_service('RAM', True,
                f'{ram_used_gb:.1f} Go / {ram_total_gb:.1f} Go'))
        except Exception:
            checks.append(_check_service('RAM', True, 'Non disponible'))
        try:
            load = os.getloadavg()
            checks.append(_check_service('CPU (load)', True,
                f'Load: {load[0]:.1f} / {load[1]:.1f} / {load[2]:.1f}'))
        except Exception:
            checks.append(_check_service('CPU', True, 'Non disponible'))
    except Exception as e:
        checks.append(_check_service('CPU', True, str(e)))

    # ── Health response time ──
    try:
        import time
        t0 = time.time()
        from flask import url_for
        with current_app.test_client() as c:
            resp = c.get(url_for('main.health'))
            elapsed_ms = (time.time() - t0) * 1000
        health_latency = f'{elapsed_ms:.0f} ms'
        if elapsed_ms > 1000:
            health_latency += ' ⚠ lent'
        checks.append(_check_service('/health latency', elapsed_ms < 1000,
            health_latency))
    except Exception as e:
        checks.append(_check_service('/health latency', True, str(e)))

    # ── Version info ──
    versions = {
        'Python': __import__('platform').python_version(),
        'Flask': __import__('flask').__version__,
        'SQLAlchemy': __import__('sqlalchemy').__version__,
        'PostgreSQL': '',
    }
    try:
        r = db.session.execute(db.text('SHOW server_version'))
        versions['PostgreSQL'] = r.scalar()
    except Exception:
        versions['PostgreSQL'] = '?'

    return render_template('admin/services.html', checks=checks, versions=versions, health_api=health_api, queues_info=queues_info)
