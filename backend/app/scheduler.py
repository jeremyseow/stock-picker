from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
import logging
from app.pipeline import run_analysis_pipeline

logger = logging.getLogger(__name__)

async def daily_pipeline_job():
    logger.info("Starting scheduled daily Reddit scraping and market research pipeline...")
    try:
        await run_analysis_pipeline()
        logger.info("Scheduled daily pipeline job completed successfully.")
    except Exception as e:
        logger.error(f"Error running scheduled daily pipeline job: {e}")

def setup_scheduler():
    scheduler = AsyncIOScheduler()
    # Run every day at 7:00 PM (19:00) SGT (Singapore Time)
    logger.info("Setting up daily background scheduler at 19:00 SGT (Asia/Singapore)")
    scheduler.add_job(
        daily_pipeline_job,
        'cron',
        hour=19,
        minute=0,
        timezone=ZoneInfo('Asia/Singapore')
    )
    return scheduler
