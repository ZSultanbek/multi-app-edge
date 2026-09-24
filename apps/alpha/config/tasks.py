import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def ping():
    """A deliberately boring task. The interesting part is that failures are
    logged explicitly - a task that swallows its exception reports success and
    you find out weeks later that nothing has run."""
    try:
        logger.info("ping task executed")
        return "pong"
    except Exception:
        logger.exception("ping task failed")
        raise
