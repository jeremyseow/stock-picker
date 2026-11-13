import logging
from typing import List, Dict, Any
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    get_latest_smart_money_tickers,
    get_latest_options_whale_tickers,
    get_latest_core_equity_report,
    get_latest_retail_report,
    get_latest_smart_money_report,
    get_latest_options_whale_report,
    get_insider_trades_by_ticker,
    get_congress_trades_by_ticker,
    save_synthesis_reports,
)
from app.models import DailyTicker, RetailSentimentReport, OptionsWhaleTicker
from app.scoring_weights import get_synthesis_weights
from sqlalchemy.future import select
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)


def calculate_timing_edge(retail_mentions: int, conviction_score: float, archetype: str = "Silent Accumulation") -> tuple[float, str]:
    """Calculates timing edge score (0-100) and retail awareness level."""
    sw = get_synthesis_weights()
    stealth_base = float(sw.get("stealth_timing_edge_base", 95.0))
    decay_mult = float(sw.get("retail_decay_multiplier", 2.0))
    rocket_edge = float(sw.get("rocket_timing_edge", 50.0))
    trap_edge = float(sw.get("retail_trap_timing_edge", 15.0))

    if archetype == "Silent Accumulation":
        if retail_mentions == 0:
            return stealth_base, "Zero Awareness (Stealth)"
        return max(85.0 - retail_mentions * decay_mult, 70.0), "Early Discovery"
    elif archetype == "The Rocket":
        return rocket_edge, "High Awareness"
    elif archetype == "The Retail Trap":
        return trap_edge, "Saturated Hype"
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

    # Fetch latest Engine 1 reports for sentiment & report FK linkage
    e1_reports = {}
    for ticker in e1_tickers:
        rep = await get_latest_retail_report(db, ticker)
        if rep:
            e1_reports[ticker] = {
                "id": rep.id,
                "sentiment": rep.community_sentiment,
                "recommendation": rep.recommendation,
            }

    # 2. Fetch latest Engine 2 tickers & reports
    e2_tickers_list = await get_latest_smart_money_tickers(db)
    e2_tickers = {}
    for sm in e2_tickers_list:
        sym = sm.ticker.upper()
        sm_rep = await get_latest_smart_money_report(db, sym)
        e2_tickers[sym] = {
            "report_id": sm_rep.id if sm_rep else None,
            "rank": sm.rank,
            "conviction": sm.conviction_score,
            "cluster_count": sm.cluster_count,
            "volume": sm.total_buy_volume,
            "buyer_summary": sm.top_buyer_summary,
        }

    # 3. Fetch latest Engine 3 (Whale Options) tickers & reports
    e3_tickers_list = await get_latest_options_whale_tickers(db)
    e3_tickers = {}
    for ow in e3_tickers_list:
        sym = ow.ticker.upper()
        ow_rep = await get_latest_options_whale_report(db, sym)
        e3_tickers[sym] = {
            "report_id": ow_rep.id if ow_rep else None,
            "rank": ow.rank,
            "whale_score": ow.whale_score,
            "unusual_oi": ow.unusual_oi_multiplier,
            "pc_ratio": ow.put_call_ratio,
            "top_strike": ow.top_strike_summary,
        }

    all_symbols = set(e1_tickers.keys()) | set(e2_tickers.keys()) | set(e3_tickers.keys())
    synthesis_results = []

    for ticker in all_symbols:
        e1_data = e1_tickers.get(ticker, {})
        e1_rep = e1_reports.get(ticker, {})
        e2_data = e2_tickers.get(ticker, {})
        e3_data = e3_tickers.get(ticker, {})

        mentions = e1_data.get("mentions", 0)
        sentiment = e1_rep.get("sentiment", "Unmonitored")
        conviction = e2_data.get("conviction", 0.0)
        whale_score = e3_data.get("whale_score", 0.0)
        pc_ratio = e3_data.get("pc_ratio", 1.0)

        # Evaluate Form 4 insider selling strictly from Engine 2's insider_trades_raw
        insider_rows = await get_insider_trades_by_ticker(db, ticker, limit=25)
        buy_val = sum((r.total_value or 0.0) for r in insider_rows if r.transaction_type == "BUY")
        sell_val = sum((r.total_value or 0.0) for r in insider_rows if r.transaction_type == "SELL")
        buy_sh = sum((r.shares or 0.0) for r in insider_rows if r.transaction_type == "BUY")
        sell_sh = sum((r.shares or 0.0) for r in insider_rows if r.transaction_type == "SELL")
        is_insider_selling = bool(
            insider_rows and (sell_val > buy_val or (sell_sh > buy_sh and sell_sh > 0))
        )

        # Evaluate Congressional sales
        congress_rows = await get_congress_trades_by_ticker(db, ticker, limit=15)
        has_congress_sells = any((c.transaction_type or "").upper() == "SELL" for c in congress_rows)
        is_distribution = is_insider_selling or has_congress_sells

        # Classify Signals
        is_high_retail = mentions >= 10 or e1_data.get("rank") is not None
        is_high_smart_money = conviction >= 20.0 or e2_data.get("cluster_count", 0) >= 2
        is_whale_bullish = whale_score >= 40.0 and pc_ratio <= 0.65
        is_whale_bearish = pc_ratio >= 1.5 and whale_score >= 25.0

        # Triangulation Archetype Classification
        if is_high_retail and (is_distribution or is_whale_bearish):
            archetype = "The Retail Trap"
            action = "AVOID/SHORT"
            trap_reasons = []
            if is_insider_selling:
                trap_reasons.append("insider selling")
            if has_congress_sells:
                trap_reasons.append("congressional selling")
            if is_whale_bearish:
                trap_reasons.append(f"bearish whale put skew (P/C {pc_ratio:.2f})")
            diagnosis = (
                f"Retail hype is elevated ({mentions} mentions), but institutional flow indicates "
                f"{' and '.join(trap_reasons)}. High risk of retail acting as exit liquidity."
            )
        elif not is_high_retail and is_high_smart_money and is_whale_bullish:
            archetype = "Silent Accumulation"
            action = "STRONG STEALTH BUY"
            diagnosis = (
                f"Institutional Triangulation confirmed: Form 4 insiders and aggressive options whale sweeps "
                f"(Score: {whale_score:.1f}) are quietly accumulating while Reddit attention is near zero ({mentions} mentions)."
            )
        elif not is_high_retail and (is_high_smart_money or is_whale_bullish):
            archetype = "Silent Accumulation"
            action = "EARLY SWING BUY"
            source = "options whale call sweeps" if is_whale_bullish else "smart money insider buying"
            diagnosis = (
                f"High-conviction {source} (Score: {max(conviction, whale_score):.1f}) with near-zero Reddit attention "
                f"({mentions} mentions). Asymmetric pre-catalyst timing edge."
            )
        elif is_high_retail and (is_high_smart_money or is_whale_bullish):
            archetype = "The Rocket"
            action = "STRONG BUY"
            diagnosis = (
                f"Full Alignment detected: Retail momentum ({mentions} mentions) is validated by institutional "
                f"conviction (Insider Conviction: {conviction:.1f}, Whale Score: {whale_score:.1f})."
            )
        else:
            archetype = "Market Noise"
            action = "PASS"
            diagnosis = "Routine market chatter without significant insider or options whale convergence."

        timing_edge, awareness = calculate_timing_edge(mentions, max(conviction, whale_score), archetype)
        core_intel = await get_latest_core_equity_report(db, ticker)

        whale_flow_label = None
        if e3_data:
            if is_whale_bullish:
                whale_flow_label = f"Bullish Call Sweeps ({e3_data.get('top_strike', '')})"
            elif is_whale_bearish:
                whale_flow_label = f"Bearish Put Skew (P/C {pc_ratio:.2f})"
            else:
                whale_flow_label = "Neutral Options Tape"

        flow_label = e2_data.get("buyer_summary") or (
            "Bearish Divergence: Insider & Lawmaker Selling" if is_distribution else "Neutral"
        )

        synthesis_results.append({
            "ticker": ticker,
            "core_intel_id": core_intel.id if core_intel else None,
            "retail_report_id": e1_rep.get("id"),
            "smart_money_report_id": e2_data.get("report_id"),
            "options_whale_report_id": e3_data.get("report_id"),
            "archetype": archetype,
            "retail_rank": e1_data.get("rank"),
            "retail_mentions": mentions,
            "retail_sentiment": sentiment,
            "smart_money_rank": e2_data.get("rank"),
            "smart_money_conviction": conviction,
            "smart_money_flow": flow_label,
            "retail_awareness_level": awareness,
            "timing_edge_score": timing_edge,
            "synthesis_diagnosis": diagnosis,
            "recommended_action": action,
            "whale_options_flow": whale_flow_label,
            "whale_options_score": whale_score,
            "put_call_ratio": pc_ratio if e3_data else None,
        })

    # Sort by timing edge descending
    synthesis_results = sorted(synthesis_results, key=lambda x: x["timing_edge_score"], reverse=True)

    # Persist to database
    await save_synthesis_reports(db, synthesis_results)
    logger.info(f"Cross-Engine Synthesis completed: {len(synthesis_results)} records generated.")
    return synthesis_results
