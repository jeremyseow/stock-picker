from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
import logging
from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.synthesis_engine import generate_cross_engine_synthesis
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def daily_pipeline_job():
    logger.info("Starting scheduled daily Dual-Engine market intelligence pipeline...")
    try:
        logger.info("Executing Engine 1: Retail Momentum...")
        await run_analysis_pipeline()

        logger.info("Executing Engine 2: Smart Money & Political Scout...")
        await run_smart_money_pipeline()

        logger.info("Executing Cross-Engine Synthesis Hub...")
        async with AsyncSessionLocal() as db:
            await generate_cross_engine_synthesis(db)

        logger.info("Scheduled daily dual-engine pipeline completed successfully.")
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
