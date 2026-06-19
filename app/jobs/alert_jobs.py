from app.services.alert_engine import run_daily_alerts


def run_alerts_job():
    """Wrapper RQ pour exécuter les alertes quotidiennes."""
    return run_daily_alerts()
