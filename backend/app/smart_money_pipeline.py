import logging
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.smart_money_ingestor import ingest_all_smart_money
from app.smart_money_scorer import rank_smart_money_candidates
from app.smart_money_researcher import research_smart_money_candidate
from app.crud import save_smart_money_tickers, save_smart_money_report
from app.synthesis_engine import generate_cross_engine_synthesis

logger = logging.getLogger(__name__)
_smart_money_lock = asyncio.Lock()


async def run_smart_money_pipeline(limit: int = 5) -> list[dict]:
    """
    Executes Engine 2 (Smart Money & Political Scout):
    1. Ingests Form 4 cash purchases & Congressional disclosures.
    2. Scores and filters candidates down to top `limit` stocks.
    3. Researches legislative, macro, and corporate catalysts.
    4. Persists records to database.
    """
    if _smart_money_lock.locked():
        logger.warning("Engine 2 (Smart Money Scout) is already running. Skipping concurrent run.")
        return []

    async with _smart_money_lock:
        logger.info("Starting Engine 2: Smart Money & Political Scout...")
        await init_db()

        # Step 1: Ingestion
        raw_data = await ingest_all_smart_money()
        insiders = raw_data.get("insider_trades", [])
        congress = raw_data.get("congress_trades", [])
        logger.info(f"Ingested {len(insiders)} insider trades and {len(congress)} Congressional disclosures.")

        # Step 2: Scoring & Filtering
        top_candidates = rank_smart_money_candidates(insiders, congress, limit=limit)
        if not top_candidates:
            logger.warning("No qualifying smart money candidates found.")
            return []

        # Step 3: Persistence of Tickers
        async with AsyncSessionLocal() as db:
            await save_smart_money_tickers(db, top_candidates)

        # Step 4: Research & Report Generation
        reports = []
        async with AsyncSessionLocal() as db:
            for c in top_candidates:
                report_data = await research_smart_money_candidate(c)
                await save_smart_money_report(db, report_data)
                reports.append(report_data)

        # Step 5: Refresh Cross-Engine Synthesis
        logger.info("Step 5: Refreshing Cross-Engine Synthesis Matrix...")
        try:
            async with AsyncSessionLocal() as db:
                await generate_cross_engine_synthesis(db)
        except Exception as e:
            logger.warning(f"Could not refresh cross-engine synthesis after Engine 2: {e}")

        logger.info(f"Engine 2 completed successfully: {len(reports)} reports generated.")
        return reports

