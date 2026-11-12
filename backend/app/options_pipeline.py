import logging
import asyncio
from datetime import timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.options_scraper import fetch_options_data_for_ticker
from app.options_scorer import rank_whale_candidates
from app.core_intel_engine import research_core_equity_intel
from app.crud import (
    save_options_whale_tickers,
    save_options_whale_report,
    get_latest_smart_money_tickers,
    get_distinct_tracked_tickers,
)
from app.models import DailyTicker, OptionsWhaleReport
from sqlalchemy.future import select
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Core benchmark and liquid mega-cap options candidates to always monitor for whale sweeps
DEFAULT_OPTIONS_UNIVERSE = [
    "NVDA", "TSLA", "AAPL", "AMD", "PLTR", "AMZN", "META", "MSFT", "GOOG", "SMCI"
]


async def run_options_pipeline(
    candidate_tickers: Optional[List[str]] = None,
    limit: int = 5,
    db: Optional[AsyncSession] = None,
) -> List[OptionsWhaleReport]:
    """
    Orchestrates Engine 3: Institutional Whale Options Radar.
    1. Gathers candidate pool from Engine 1, Engine 2, and liquid options universe.
    2. Fetches option chains & detects unusual Volume > 2.5x OI and OTM call sweeps.
    3. Scores and ranks top whale options candidates.
    4. Attaches shared CoreEquityReport fundamental ground truth.
    5. Saves records to options_whale_tickers and options_whale_reports.
    """
    logger.info("Starting Engine 3: Institutional Whale Options Radar pipeline...")

    should_close = False
    if db is None:
        db = AsyncSessionLocal()
        should_close = True

    try:
        pool = set(candidate_tickers or [])

        # Add latest Engine 1 (Retail) tickers
        e1_subq = select(func.max(DailyTicker.date))
        e1_ts = (await db.execute(e1_subq)).scalar_one_or_none()
        if e1_ts:
            e1_q = select(DailyTicker.ticker).where(DailyTicker.date >= e1_ts - timedelta(minutes=2))
            for sym in (await db.execute(e1_q)).scalars().all():
                pool.add(sym.upper())

        # Add latest Engine 2 (Smart Money) tickers
        sm_tickers = await get_latest_smart_money_tickers(db)
        for sm in sm_tickers:
            pool.add(sm.ticker.upper())

        # Fallback to liquid options universe if pool is small
        for sym in DEFAULT_OPTIONS_UNIVERSE:
            if len(pool) < 15:
                pool.add(sym)

        logger.info(f"Scanning options chains across {len(pool)} equity candidates: {sorted(list(pool))}")

        # Scan option chains concurrently with asyncio.to_thread to avoid blocking event loop
        tasks = [asyncio.to_thread(fetch_options_data_for_ticker, sym) for sym in pool]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        scanned_data = []
        for res in results:
            if isinstance(res, dict) and res.get("ticker"):
                scanned_data.append(res)
            elif isinstance(res, Exception):
                logger.debug(f"Options scraping exception: {res}")

        # Rank candidates by Whale Conviction Score
        ranked_candidates = rank_whale_candidates(scanned_data, limit=limit)
        if not ranked_candidates:
            logger.info("No unusual options flow detected above threshold today.")
            return []

        logger.info(f"Identified top {len(ranked_candidates)} Whale Options candidates: {[c['ticker'] for c in ranked_candidates]}")

        # Save top ticker rows
        saved_tickers = await save_options_whale_tickers(db, ranked_candidates)

        # Generate individual reports linked with CoreEquityReport and OptionsWhaleTicker
        saved_reports: List[OptionsWhaleReport] = []
        for idx, candidate in enumerate(ranked_candidates):
            sym = candidate["ticker"]
            try:
                # Link or generate CoreEquityReport
                core_intel = await research_core_equity_intel(sym, db=db)
                ow_ticker_id = saved_tickers[idx].id if idx < len(saved_tickers) else None
                report = await save_options_whale_report(
                    db=db,
                    ticker=sym,
                    whale_data=candidate,
                    core_intel_id=core_intel.get("id") if isinstance(core_intel, dict) else (core_intel.id if core_intel else None),
                    options_whale_ticker_id=ow_ticker_id,
                    rank=candidate.get("rank"),
                )
                saved_reports.append(report)
            except Exception as e:
                logger.error(f"Failed to generate Options Whale report for ${sym}: {e}", exc_info=True)

        logger.info(f"Successfully generated and stored {len(saved_reports)} Options Whale reports.")
        return saved_reports

    finally:
        if should_close:
            await db.close()
