import logging
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.smart_money_ingestor import ingest_all_smart_money
from app.smart_money_scorer import rank_smart_money_candidates
from app.smart_money_researcher import research_smart_money_candidate
from app.core_intel_engine import research_core_equity_intel
from app.crud import save_smart_money_tickers, save_smart_money_report

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
            for idx, c in enumerate(top_candidates):
                ticker = c["ticker"]
                logger.info(f"Conducting Core Equity Intel for Smart Money candidate ${ticker}...")
                core_intel = await research_core_equity_intel(ticker, db=db)

                logger.info(f"Generating Smart Money Catalyst report for ${ticker}...")
                report_data = await research_smart_money_candidate(c)
                report_data["rank"] = idx + 1
                report_data["ground_truth_status"] = core_intel.get("ground_truth_status")
                report_data["ground_truth_filings_news"] = core_intel.get("ground_truth_filings_news")
                report_data["events_happenings"] = core_intel.get("events_happenings")
                report_data["risk_score"] = core_intel.get("risk_score")
                report_data["raw_metrics"] = core_intel.get("raw_metrics") or report_data.get("raw_metrics", {})
                if not report_data.get("current_price") and core_intel.get("current_price"):
                    report_data["current_price"] = core_intel.get("current_price")
                if not report_data.get("target_price") and core_intel.get("target_price"):
                    report_data["target_price"] = core_intel.get("target_price")

                await save_smart_money_report(db, report_data, core_intel_id=core_intel.get("id"))
                reports.append(report_data)

        logger.info(f"Engine 2 completed successfully: {len(reports)} reports generated.")
        return reports

