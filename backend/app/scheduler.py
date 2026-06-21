from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logger = logging.getLogger(__name__)

async def daily_pipeline_job():
    logger.info("Starting daily Reddit scraping and market research pipeline...")
    # TODO: Call scraping logic here
    pass

def setup_scheduler():
    scheduler = AsyncIOScheduler()
    # Run every day at 00:00 UTC
    scheduler.add_job(daily_pipeline_job, 'cron', hour=0, minute=0)
    return scheduler
