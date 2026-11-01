import asyncio
import logging
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.synthesis_engine import generate_cross_engine_synthesis
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_pipeline")


async def main():
    logger.info("=== [Step 1/3: Engine 1 (Retail Momentum)] Starting... ===")
    await run_analysis_pipeline()

    logger.info("=== [Step 2/3: Engine 2 (Smart Money Scout)] Starting... ===")
    await run_smart_money_pipeline(limit=5)

    logger.info("=== [Step 3/3: Cross-Engine Synthesis Matrix] Correlating signals... ===")
    async with AsyncSessionLocal() as db:
        await generate_cross_engine_synthesis(db)

    logger.info("All pipelines and synthesis reports generated successfully!")


if __name__ == "__main__":
    asyncio.run(main())
