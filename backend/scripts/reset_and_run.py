import asyncio
import sys
import os
from pathlib import Path
import argparse
import logging

# Ensure backend root is on sys.path regardless of execution working directory
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import engine, Base, init_db, AsyncSessionLocal
from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.synthesis_engine import generate_cross_engine_synthesis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reset_and_run")


async def reset_database():
    """Drops all tables and initializes clean schema."""
    logger.info("Dropping all existing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database reset complete. All tables freshly initialized.")


async def main():
    parser = argparse.ArgumentParser(description="Reset database and/or run dual-engine market intelligence pipelines.")
    parser.add_argument("--reset-only", action="store_true", help="Only clear/reset database without running pipelines.")
    parser.add_argument("--skip-engine1", action="store_true", help="Skip Engine 1 (Retail Momentum).")
    parser.add_argument("--skip-engine2", action="store_true", help="Skip Engine 2 (Smart Money Scout).")
    args = parser.parse_args()

    # Step 1: Reset database
    await reset_database()
    if args.reset_only:
        logger.info("Reset-only flag provided. Exiting.")
        return

    # Step 2: Run Engine 1 (Retail Momentum)
    if not args.skip_engine1:
        logger.info("=== [Engine 1: Retail Momentum] Starting... ===")
        try:
            await run_analysis_pipeline()
            logger.info("=== [Engine 1: Retail Momentum] Completed successfully. ===")
        except Exception as e:
            logger.error(f"Engine 1 failed: {e}", exc_info=True)

    # Step 3: Run Engine 2 (Smart Money & Political Scout)
    if not args.skip_engine2:
        logger.info("=== [Engine 2: Smart Money Scout] Starting... ===")
        try:
            await run_smart_money_pipeline(limit=5)
            logger.info("=== [Engine 2: Smart Money Scout] Completed successfully. ===")
        except Exception as e:
            logger.error(f"Engine 2 failed: {e}", exc_info=True)

    # Step 4: Cross-Engine Synthesis
    logger.info("=== [Cross-Engine Synthesis Matrix] Correlating signals... ===")
    try:
        async with AsyncSessionLocal() as db:
            synthesis = await generate_cross_engine_synthesis(db)
        logger.info(f"=== [Cross-Engine Synthesis Matrix] Done! {len(synthesis)} archetype records generated. ===")
    except Exception as e:
        logger.error(f"Cross-engine synthesis failed: {e}", exc_info=True)

    logger.info("Dual-Engine Pipeline run completed.")


if __name__ == "__main__":
    asyncio.run(main())

