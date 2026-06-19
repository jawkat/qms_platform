"""
Worker RQ pour QMS Platform.

Lance le worker et le scheduler pour les tâches asynchrones.

Usage:
    python run_worker.py
"""
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('worker')

from app import create_app

app = create_app()

with app.app_context():
    from redis import Redis
    from rq import Queue, Worker
    from rq_scheduler import Scheduler

    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    conn = Redis.from_url(redis_url)

    logger.info('Worker connecting to Redis: %s', redis_url)
    logger.info('Redis ping: %s', conn.ping())

    # Files d'attente
    queues = [Queue('high', connection=conn), Queue('default', connection=conn), Queue('low', connection=conn)]

    # Lancer le worker
    worker = Worker(queues, connection=conn, name=f'qms-worker-{os.getpid()}')
    logger.info('Starting RQ worker on queues: high, default, low')
    worker.work()
