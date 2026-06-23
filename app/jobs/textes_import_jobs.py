def run_textes_import(payloads, link_to_enterprise, user_id, entreprise_id):
    from app.textes.routes.import_export import _process_json_bundle_entries
    result = _process_json_bundle_entries(
        payloads,
        dry_run=False,
        link_to_enterprise=link_to_enterprise,
        user_id=user_id,
        entreprise_id=entreprise_id,
    )
    successes = result.get('successes') or []
    failures = result.get('failures') or []
    if successes:
        from app.services.notification_service import NotificationService
        total_articles = result.get('total_articles', 0)
        message = (
            f"Import JSON termin\u00e9\u00a0: {len(successes)} fichier(s), "
            f"{total_articles} article(s) cr\u00e9\u00e9(s)."
        )
        if failures:
            message += f" {len(failures)} fichier(s) en erreur."
        entite_id = successes[0]['result']['texte_id'] if len(successes) == 1 else None
        NotificationService.notify(
            utilisateur_id=user_id,
            category='systeme',
            message=message,
            urgence='normale',
            entite_type='texte',
            entite_id=entite_id,
            notification_type='import_texte',
            skip_module_check=True,
        )
    return result


def enqueue_textes_import(payloads, link_to_enterprise, user_id, entreprise_id):
    from redis import Redis
    from rq import Queue
    from flask import current_app
    url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(url)
    q = Queue('default', connection=conn)
    job = q.enqueue(
        run_textes_import,
        payloads,
        link_to_enterprise,
        user_id,
        entreprise_id,
        job_timeout=600,
    )
    return job.id


def get_job_status(job_id):
    from redis import Redis
    from rq.job import Job
    from flask import current_app
    url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(url)
    try:
        job = Job.fetch(job_id, connection=conn)
        return {
            'status': job.get_status(),
            'result': job.result,
            'error': str(job.exc_info) if job.exc_info else None,
            'meta': job.meta,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'enqueued_at': job.enqueued_at.isoformat() if job.enqueued_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
        }
    except Exception as exc:
        return {'status': 'unknown', 'error': str(exc)}
