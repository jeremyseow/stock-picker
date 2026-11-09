from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.pipeline import run_full_pipeline
from app.database import AsyncSessionLocal
from app.portfolio_engine import execute_market_open_orders, evaluate_market_close_exits

logger = logging.getLogger(__name__)

# Ensure apscheduler logs are captured
logging.getLogger("apscheduler").setLevel(logging.INFO)

TIMEZONE_SGT = ZoneInfo("Asia/Singapore")
TIMEZONE_ET = ZoneInfo("America/New_York")


async def daily_pipeline_job():
    """Daily execution of the full Multi-Engine intelligence pipeline."""
    logger.info("Starting scheduled daily Multi-Engine market intelligence pipeline...")
    try:
        await run_full_pipeline(limit=5)
        logger.info("Scheduled daily multi-engine pipeline completed successfully.")
    except Exception as e:
        logger.exception(f"Error running scheduled daily pipeline job: {e}")


async def market_open_execution_job():
    """Scheduled US Market Open (09:30 ET) order execution."""
    logger.info("Executing scheduled US Market Open paper portfolio orders...")
    try:
        async with AsyncSessionLocal() as session:
            res = await execute_market_open_orders(session)
            logger.info(f"Market open execution completed: {res.get('executed_count', 0)} orders executed.")
    except Exception as e:
        logger.exception(f"Error executing scheduled market open orders: {e}")


async def market_close_evaluation_job():
    """Scheduled US Market Close (16:00 ET) position evaluation & mark-to-market."""
    logger.info("Evaluating scheduled US Market Close paper portfolio exits and snapshots...")
    try:
        async with AsyncSessionLocal() as session:
            res = await evaluate_market_close_exits(session)
            logger.info(f"Market close evaluation completed: {res.get('closed_count', 0)} closed, {res.get('updated_count', 0)} updated.")
    except Exception as e:
        logger.exception(f"Error evaluating scheduled market close exits: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """Configures the AsyncIOScheduler with resilient misfire and timezone settings."""
    scheduler = AsyncIOScheduler(timezone=TIMEZONE_SGT)
    
    # 1. Run pipeline every day at 7:00 PM (19:00) SGT (Singapore Time)
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

    # 2. Run US Market Open order execution Monday-Friday at 09:30 ET
    logger.info("Setting up US Market Open order execution at 09:30 ET (America/New_York)")
    scheduler.add_job(
        market_open_execution_job,
        'cron',
        day_of_week='mon-fri',
        hour=9,
        minute=30,
        timezone=TIMEZONE_ET,
        id="us_market_open_order_execution",
        name="US Market Open Order Execution",
        misfire_grace_time=3600,
        coalesce=True,
        replace_existing=True
    )

    # 3. Run US Market Close exit evaluation Monday-Friday at 16:00 ET
    logger.info("Setting up US Market Close exit evaluation at 16:00 ET (America/New_York)")
    scheduler.add_job(
        market_close_evaluation_job,
        'cron',
        day_of_week='mon-fri',
        hour=16,
        minute=0,
        timezone=TIMEZONE_ET,
        id="us_market_close_exit_evaluation",
        name="US Market Close Exit Evaluation",
        misfire_grace_time=3600,
        coalesce=True,
        replace_existing=True
    )

    return scheduler
