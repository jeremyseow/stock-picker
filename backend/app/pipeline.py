import logging
from app.database import AsyncSessionLocal
from app.retail_pipeline import run_retail_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.options_pipeline import run_options_pipeline
from app.synthesis_engine import generate_cross_engine_synthesis

logger = logging.getLogger(__name__)


async def run_full_pipeline(limit: int = 5):
    """
    Executes the full end-to-end multi-engine market intelligence pipeline:
    1. Engine 1: Retail Momentum Scout (Reddit sentiment & overlays)
    2. Engine 2: Smart Money & Political Scout (Form 4 & Congressional disclosures)
    3. Engine 3: Institutional Whale Options Radar (unusual Volume/OI sweeps)
    4. Cross-Engine Synthesis Hub: 3-Way Triangulation Archetype matrix
    """
    logger.info("==================================================")
    logger.info("Starting Full Multi-Engine Market Intelligence Pipeline...")
    logger.info("==================================================")

    # 1. Run Engine 1: Retail Momentum
    logger.info("--- [1/4] Running Engine 1: Retail Momentum Scout ---")
    await run_retail_pipeline()

    # 2. Run Engine 2: Smart Money & Politics
    logger.info("--- [2/4] Running Engine 2: Smart Money Scout ---")
    await run_smart_money_pipeline(limit=limit)

    # 3. Run Engine 3: Whale Options Radar
    logger.info("--- [3/4] Running Engine 3: Institutional Whale Options Radar ---")
    await run_options_pipeline(limit=limit)

    # 4. Run Cross-Engine Synthesis
    logger.info("--- [4/4] Running Cross-Engine Triangulation Synthesis ---")
    async with AsyncSessionLocal() as db:
        await generate_cross_engine_synthesis(db)

    logger.info("==================================================")
    logger.info("All pipelines and synthesis completed successfully!")
    logger.info("==================================================")
