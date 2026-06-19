"""
Scheduler pour les tâches périodiques QMS Platform.

Lance les alertes quotidiennes et les envois d'emails via RQ.

Usage (dans le worker ou en standalone):
    python -m app.jobs.scheduler

Ou via RQ:
    from app.jobs.scheduler import schedule_daily_tasks
    schedule_daily_tasks()
"""
import logging
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_scheduler(redis_url=None):
    """Retourne un scheduler RQ connecté à Redis."""
    from flask import current_app
    url = redis_url or current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(url)
    return Scheduler(connection=conn, queue_name='default')


def schedule_daily_tasks(redis_url=None):
    """Planifie les tâches quotidiennes."""
    from app.jobs.alert_jobs import run_alerts_job
    from app.jobs.mail_jobs import send_action_reminder_email

    scheduler = get_scheduler(redis_url)

    # Supprimer les anciens jobs planifiés
    try:
        for job in scheduler.get_jobs():
            if hasattr(job, 'meta') and job.meta.get('type') == 'daily':
                scheduler.cancel(job)
    except Exception:
        pass

    # Alerte quotidienne à 8h00
    scheduler.schedule(
        scheduled_time=datetime.utcnow().replace(hour=8, minute=0, second=0),
        func=run_alerts_job,
        interval=86400,  # 24h
        meta={'type': 'daily', 'name': 'daily_alerts'},
    )
    logger.info('Scheduled daily alerts at 08:00 UTC')


def enqueue_email(subject, recipients, html, sender=None, priority='default'):
    """Enfile un email dans la queue RQ pour envoi asynchrone."""
    from app.jobs.mail_jobs import send_async_email

    url = None
    try:
        from flask import current_app
        url = current_app.config.get('REDIS_URL')
    except RuntimeError:
        pass

    conn = Redis.from_url(url or 'redis://localhost:6379/0')
    q = Queue(priority, connection=conn)

    job = q.enqueue(
        send_async_email,
        subject, recipients, html, sender,
        job_timeout='5m',
    )
    logger.info('Email enqueued: job=%s subject=%s', job.id, subject)
    return job


def run_scheduler_standalone():
    """Lance le scheduler en mode standalone (pour docker-compose worker)."""
    from app import create_app

    app = create_app()
    with app.app_context():
        schedule_daily_tasks(app.config.get('REDIS_URL'))
        logger.info('Scheduler started')

        scheduler = get_scheduler(app.config.get('REDIS_URL'))
        scheduler.run()
