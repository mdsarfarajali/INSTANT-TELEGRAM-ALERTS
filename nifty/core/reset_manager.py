import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from nifty.storage.database import reset_levels as reset_nifty
import xauusd.storage.database as xauusd_db
from config.settings import settings

logger = logging.getLogger(__name__)


async def scheduled_reset():
    """Wrapper that runs reset for all instruments and logs it."""
    logger.info("Running scheduled daily level reset for NIFTY and XAUUSD...")
    await reset_nifty()
    await xauusd_db.reset_levels()
    logger.info("Daily reset complete — all levels for all instruments deactivated.")


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

    # Parse reset time from settings (e.g. "09:00")
    try:
        hour, minute = map(int, settings.RESET_TIME_IST.split(":"))
    except ValueError:
        logger.warning("Invalid RESET_TIME_IST format, defaulting to 09:00")
        hour, minute = 9, 0

    scheduler.add_job(
        scheduled_reset,
        CronTrigger(hour=hour, minute=minute, timezone="Asia/Kolkata"),
        id="daily_reset",
        name="Daily Level Reset",
        replace_existing=True,
        misfire_grace_time=60,
    )

    logger.info(f"Scheduler configured: daily reset at {hour:02d}:{minute:02d} IST")
    return scheduler
