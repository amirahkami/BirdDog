from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import get_settings
from app.cv.processor import process_cv_facts_batch, process_cv_work_batch
from app.worker.tasks import run_daily_pipeline


def create_scheduler() -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(
        process_cv_work_batch,
        IntervalTrigger(seconds=settings.cv_worker_interval_seconds),
        id="cv-processing",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        process_cv_facts_batch,
        IntervalTrigger(seconds=settings.cv_facts_worker_interval_seconds),
        id="cv-facts",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_daily_pipeline,
        CronTrigger.from_crontab(settings.schedule_cron, timezone=settings.timezone),
        id="daily-job-pipeline",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler
