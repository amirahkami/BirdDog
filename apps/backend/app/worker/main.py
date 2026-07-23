import logging

from app.core.config import get_settings
from app.worker.scheduler import create_scheduler


def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    scheduler = create_scheduler()
    logging.getLogger(__name__).info(
        "BirdDog worker started with schedule %s (%s)",
        settings.schedule_cron,
        settings.timezone,
    )
    scheduler.start()


if __name__ == "__main__":
    main()
