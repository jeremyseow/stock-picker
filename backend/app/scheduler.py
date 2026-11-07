from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
import logging
from pathlib import Path
from dotenv import load_dotenv
from app.pipeline import run_full_pipeline

logger = logging.getLogger(__name__)

# Ensure apscheduler logs are captured
logging.getLogger("apscheduler").setLevel(logging.INFO)

TIMEZONE_SGT = ZoneInfo("Asia/Singapore")


async def daily_pipeline_job():
    """Daily execution of the full Multi-Engine intelligence pipeline."""
    logger.info("Starting scheduled daily Multi-Engine market intelligence pipeline...")
    try:
        await run_full_pipeline(limit=5)
        logger.info("Scheduled daily multi-engine pipeline completed successfully.")
    except Exception as e:
        logger.exception(f"Error running scheduled daily pipeline job: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """Configures the AsyncIOScheduler with resilient misfire and timezone settings."""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE_SGT)
    
    # Run every day at 7:00 PM (19:00) SGT (Singapore Time)
    logger.info("Setting up daily background scheduler at 19:00 SGT (Asia/Singapore)")
    scheduler.add_job(
        daily_pipeline_job,
        'cron',
        hour=19,
        minute=0,
        timezone=TIMEZONE_SGT,
        id="daily_market_intelligence_pipeline",
        name="Daily Multi-Engine Intelligence Pipeline",
        misfire_grace_time=3600,  # 1-hour grace window to survive sleep/event loop delays
        coalesce=True,            # Combine missed runs into a single run
        replace_existing=True
    )
    return scheduler

