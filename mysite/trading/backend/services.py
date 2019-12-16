from celery.schedules import crontab
from celery.task import periodic_task
from .get_nyse_data import save_nyse_tickers


@periodic_task(run_every=crontab(hour=3, minute=0,))
def ever_morning():
    save_nyse_tickers()