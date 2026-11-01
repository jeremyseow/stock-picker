import logging
from typing import List, Dict, Any
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    get_latest_smart_money_tickers,
    get_latest_core_equity_intel,
    save_synthesis_records,
)
from app.models import DailyTicker, TickerReport
from sqlalchemy.future import select
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)


def calculate_timing_edge(retail_mentions: int, conviction_score: float, archetype: str = "Silent Accumulation") -> tuple[float, str]:
    """Calculates timing edge score (0-100) and retail awareness level."""
    if archetype == "Silent Accumulation":
        if retail_mentions == 0:
            return 95.0, "Zero Awareness (Stealth)"
        return max(85.0 - retail_mentions * 2, 70.0), "Early Discovery"
    elif archetype == "The Rocket":
        return 50.0, "High Awareness"
    elif archetype == "The Retail Trap":
        return 15.0, "Saturated Hype"
    else:  # Market Noise
        return 30.0, "Emerging"


async def generate_cross_engine_synthesis(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Correlates Engine 1 (Retail Momentum) and Engine 2 (Smart Money Scout)
    to classify active tickers into the 4 market archetypes.
    """
    logger.info("Executing Cross-Engine Synthesis correlation...")

    # 1. Fetch latest Engine 1 tickers
    e1_subq = select(func.max(DailyTicker.date))
    e1_ts = (await db.execute(e1_subq)).scalar_one_or_none()
    e1_tickers = {}
    if e1_ts:
        q = select(DailyTicker).where(DailyTicker.date >= e1_ts - timedelta(minutes=2))
        for t in (await db.execute(q)).scalars().all():
            e1_tickers[t.ticker.upper()] = {
                "rank": t.rank,
                "mentions": t.mention_count,
                "engagement": t.engagement_score,
            }

    # Fetch latest Engine 1 reports for sentiment & verdicts
    e1_reports = {}
    for ticker in e1_tickers:
        rep_q = select(TickerReport).where(TickerReport.ticker == ticker).order_by(desc(TickerReport.date)).limit(1)
        rep = (await db.execute(rep_q)).scalar_one_or_none()
        if rep:
            e1_reports[ticker] = {
                "sentiment": rep.community_sentiment,
                "smart_money_verdict": rep.smart_money_verdict,
                "recommendation": rep.recommendation,
            }

    # 2. Fetch latest Engine 2 tickers & reports
    e2_tickers_list = await get_latest_smart_money_tickers(db)
    e2_tickers = {}
    for sm in e2_tickers_list:
        e2_tickers[sm.ticker.upper()] = {
            "rank": sm.rank,
            "conviction": sm.conviction_score,
            "cluster_count": sm.cluster_count,
            "volume": sm.total_buy_volume,
            "buyer_summary": sm.top_buyer_summary,
        }

    all_symbols = set(e1_tickers.keys()) | set(e2_tickers.keys())
    synthesis_results = []

    for ticker in all_symbols:
        e1_data = e1_tickers.get(ticker, {})
        e1_rep = e1_reports.get(ticker, {})
        e2_data = e2_tickers.get(ticker, {})

        mentions = e1_data.get("mentions", 0)
        sentiment = e1_rep.get("sentiment", "Unmonitored")
        conviction = e2_data.get("conviction", 0.0)
        e1_verdict = (e1_rep.get("smart_money_verdict") or "").lower()

        # Classify Archetype
        is_high_retail = mentions >= 10 or e1_data.get("rank") is not None
        is_high_smart_money = conviction >= 20.0 or e2_data.get("cluster_count", 0) >= 2
        is_insider_selling = "selling" in e1_verdict or "divergence" in e1_verdict

        if is_high_retail and is_insider_selling:
            archetype = "The Retail Trap"
            action = "AVOID/SHORT"
            diagnosis = (
                f"Retail sentiment is high ({mentions} mentions), but SEC disclosures indicate insider selling "
                "or lack of executive conviction. Retail is acting as exit liquidity."
            )
        elif is_high_retail and is_high_smart_money:
            archetype = "The Rocket"
            action = "STRONG BUY"
            diagnosis = (
                f"Full Alignment detected: Retail momentum ({mentions} mentions) is supported by "
                f"genuine insider/political conviction (Score: {conviction:.1f})."
            )
        elif not is_high_retail and is_high_smart_money:
            archetype = "Silent Accumulation"
            action = "EARLY SWING BUY"
            diagnosis = (
                f"High-conviction smart money accumulation (Score: {conviction:.1f}) with near-zero Reddit attention "
                f"({mentions} mentions). Maximum asymmetric pre-catalyst timing edge."
            )
        else:
            archetype = "Market Noise"
            action = "PASS"
            diagnosis = "Routine market discussion without significant smart money convergence."

        timing_edge, awareness = calculate_timing_edge(mentions, conviction, archetype)
        core_intel = await get_latest_core_equity_intel(db, ticker)

        synthesis_results.append({
            "ticker": ticker,
            "core_intel_id": core_intel.id if core_intel else None,
            "archetype": archetype,
            "retail_rank": e1_data.get("rank"),
            "retail_mentions": mentions,
            "retail_sentiment": sentiment,
            "smart_money_rank": e2_data.get("rank"),
            "smart_money_conviction": conviction,
            "smart_money_flow": e2_data.get("buyer_summary") or e1_rep.get("smart_money_verdict", "Neutral"),
            "retail_awareness_level": awareness,
            "timing_edge_score": timing_edge,
            "synthesis_diagnosis": diagnosis,
            "recommended_action": action,
        })

    # Sort by timing edge descending
    synthesis_results = sorted(synthesis_results, key=lambda x: x["timing_edge_score"], reverse=True)

    # Persist to database
    await save_synthesis_records(db, synthesis_results)
    logger.info(f"Cross-Engine Synthesis completed: {len(synthesis_results)} records generated.")
    return synthesis_results
