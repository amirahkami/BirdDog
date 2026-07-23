import logging

logger = logging.getLogger(__name__)


def run_daily_pipeline() -> None:
    logger.info("Daily job pipeline triggered; ingestion will be added in a later milestone")
