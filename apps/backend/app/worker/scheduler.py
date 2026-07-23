from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.worker.tasks import run_daily_pipeline


def create_scheduler() -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(
        run_daily_pipeline,
        CronTrigger.from_crontab(settings.schedule_cron, timezone=settings.timezone),
        id="daily-job-pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
