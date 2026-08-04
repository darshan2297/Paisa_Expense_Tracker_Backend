"""Celery application and beat schedule.

Workers run in a separate process from Uvicorn. Scheduled jobs (bill
reminders, digests) register here via Celery Beat.
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "paisa",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks.reminders"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "bill-reminders-daily": {
            "task": "app.worker.tasks.reminders.process_bill_reminders",
            "schedule": crontab(hour=8, minute=0),
        },
        "fixed-commitment-reminders-daily": {
            "task": "app.worker.tasks.reminders.process_fixed_commitment_reminders",
            "schedule": crontab(hour=8, minute=5),
        },
        "bill-rollover-daily": {
            "task": "app.worker.tasks.reminders.process_bill_rollover",
            "schedule": crontab(hour=0, minute=30),
        },
        "net-worth-snapshot-monthly": {
            "task": "app.worker.tasks.reminders.process_net_worth_snapshots",
            "schedule": crontab(day_of_month=1, hour=0, minute=0),
        },
    },
)
