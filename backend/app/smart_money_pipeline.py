import logging
import asyncio
from datetime import timedelta
from sqlalchemy import func
from sqlalchemy.future import select
from app.database import init_db, AsyncSessionLocal
from app.models import DailyTicker
from app.smart_money_ingestor import ingest_all_smart_money, fetch_form4_flows_for_tickers
from app.smart_money_scorer import rank_smart_money_candidates
from app.smart_money_researcher import research_smart_money_candidate
from app.core_intel_engine import research_core_equity_intel
from app.crud import (
    save_smart_money_tickers,
    save_smart_money_report,
    save_insider_trades_raw,
    save_congress_trades_raw,
)

logger = logging.getLogger(__name__)
_smart_money_lock = asyncio.Lock()


async def run_smart_money_pipeline(limit: int = 5) -> list[dict]:
    """
    Executes Engine 2 (Smart Money & Political Scout):
    1. Ingests Form 4 cash purchases, Form 4 insider flows (including SELLs), & Congressional disclosures.
    2. Scores and filters candidates down to top `limit` stocks.
    3. Researches legislative, macro, and corporate catalysts.
    4. Persists records to database with clean relational links.
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

        # Also ingest full Form 4 BUY/SELL history for latest Engine 1 trending tickers + top candidates
        saved_tickers = []
        async with AsyncSessionLocal() as db:
            e1_ts = (await db.execute(select(func.max(DailyTicker.date)))).scalar_one_or_none()
            e1_syms: list[str] = []
            if e1_ts:
                e1_q = select(DailyTicker.ticker).where(DailyTicker.date >= e1_ts - timedelta(minutes=5))
                e1_syms = [s.upper() for s in (await db.execute(e1_q)).scalars().all()]

            flow_targets = list(dict.fromkeys([c["ticker"].upper() for c in top_candidates] + e1_syms))
            form4_flows = await asyncio.to_thread(fetch_form4_flows_for_tickers, flow_targets)

            # Step 3: Persistence of Raw Evidence & Leaderboard Tickers
            all_insiders = insiders + form4_flows
            if all_insiders:
                await save_insider_trades_raw(db, all_insiders)
            if congress:
                await save_congress_trades_raw(db, congress)
            saved_tickers = await save_smart_money_tickers(db, top_candidates)

        # Step 4: Research & Report Generation
        reports = []
        async with AsyncSessionLocal() as db:
            for idx, c in enumerate(top_candidates):
                ticker = c["ticker"]
                logger.info(f"Conducting Core Equity Intel for Smart Money candidate ${ticker}...")
                core_intel = await research_core_equity_intel(ticker, db=db)

                logger.info(f"Generating Smart Money Catalyst report for ${ticker}...")
                report_data = await research_smart_money_candidate(c)
                sm_ticker_id = saved_tickers[idx].id if idx < len(saved_tickers) else None

                await save_smart_money_report(
                    db,
                    report_data,
                    core_intel_id=core_intel.get("id"),
                    smart_money_ticker_id=sm_ticker_id,
                )
                reports.append(report_data)

        logger.info(f"Engine 2 completed successfully: {len(reports)} reports generated.")
        return reports

