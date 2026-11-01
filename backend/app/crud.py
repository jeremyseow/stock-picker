from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, distinct
from datetime import timedelta
from types import SimpleNamespace
from app.models import (
    DailyTicker,
    CoreEquityIntel,
    RetailReport,
    TickerReport,
    TickerTrajectoryAnalysis,
    SmartMoneyTicker,
    SmartMoneyReport,
    SynthesisRecord,
)
from app.llm_schemas import StockReport, TrajectoryAnalysis


async def save_daily_tickers(db: AsyncSession, tickers_with_context: list):
    """
    Save the top extracted tickers to the database.
    """
    for idx, item in enumerate(tickers_with_context):
        db_ticker = DailyTicker(
            ticker=item["ticker"].upper(),
            rank=idx + 1,
            mention_count=item["mention_count"],
            engagement_score=item["engagement_score"]
        )
        db.add(db_ticker)
    await db.commit()


# ==========================================
# Core Equity Intel CRUD
# ==========================================

async def save_core_equity_intel(db: AsyncSession, intel_data: dict) -> CoreEquityIntel:
    """Save or update foundational equity intelligence for a ticker."""
    row = CoreEquityIntel(
        ticker=intel_data["ticker"].upper(),
        company_name=intel_data.get("company_name"),
        sector=intel_data.get("sector"),
        industry=intel_data.get("industry"),
        current_price=intel_data.get("current_price"),
        target_price=intel_data.get("target_price"),
        ground_truth_status=intel_data.get("ground_truth_status"),
        ground_truth_filings_news=intel_data.get("ground_truth_filings_news"),
        events_happenings=intel_data.get("events_happenings"),
        risk_score=intel_data.get("risk_score"),
        risk_analysis=intel_data.get("risk_analysis"),
        actionable_insight=intel_data.get("actionable_insight"),
        raw_metrics=intel_data.get("raw_metrics", {}),
        raw_news=intel_data.get("raw_news", []),
        raw_filings=intel_data.get("raw_filings", []),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_latest_core_equity_intel(db: AsyncSession, ticker: str) -> CoreEquityIntel | None:
    """Fetch the latest Core Equity Intel record for a ticker."""
    query = (
        select(CoreEquityIntel)
        .where(CoreEquityIntel.ticker == ticker.upper())
        .order_by(desc(CoreEquityIntel.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_core_equity_intel_by_id(db: AsyncSession, intel_id: int) -> CoreEquityIntel | None:
    """Fetch a Core Equity Intel record by ID."""
    query = select(CoreEquityIntel).where(CoreEquityIntel.id == intel_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ==========================================
# Retail Momentum Reports CRUD
# ==========================================

async def save_ticker_report(
    db: AsyncSession,
    ticker: str,
    report: StockReport,
    metrics: dict,
    news: list,
    insider_data: dict | None = None,
    core_intel_id: int | None = None,
    rank: int | None = None,
    mention_count: int = 0,
    engagement_score: float = 0.0
) -> RetailReport:
    """
    Save the generated Retail report and raw data to the database.
    """
    db_report = RetailReport(
        ticker=ticker.upper(),
        core_intel_id=core_intel_id,
        rank=rank,
        mention_count=mention_count,
        engagement_score=engagement_score,
        current_price=metrics.get("current_price"),
        target_price=metrics.get("target_price"),
        community_sentiment=report.community_sentiment,
        community_hype=report.community_hype,
        ground_truth_status=report.ground_truth_status,
        ground_truth_filings_news=report.ground_truth_filings_news,
        events_happenings=report.events_happenings,
        smart_money_verdict=report.smart_money_verdict,
        raw_insider_data=insider_data or {},
        reconciliation_risk_score=report.reconciliation_risk_score,
        reconciliation_analysis=report.reconciliation_analysis,
        reconciliation_actionable_insight=report.reconciliation_actionable_insight,
        recommendation=report.recommendation,
        recommendation_rationale=report.recommendation_rationale,
        raw_metrics=metrics,
        raw_news=news
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report


async def get_distinct_report_dates(db: AsyncSession) -> list[str]:
    """
    Returns a sorted list of unique report dates formatted as YYYY-MM-DD in descending order
    aggregated across Retail, Smart Money, and Synthesis datasets.
    """
    d1 = select(func.date(RetailReport.date)).distinct()
    d2 = select(func.date(SmartMoneyReport.date)).distinct()
    d3 = select(func.date(SynthesisRecord.date)).distinct()

    res1 = (await db.execute(d1)).scalars().all()
    res2 = (await db.execute(d2)).scalars().all()
    res3 = (await db.execute(d3)).scalars().all()

    all_dates = set([str(d) for d in res1 if d] + [str(d) for d in res2 if d] + [str(d) for d in res3 if d])
    return sorted(list(all_dates), reverse=True)


async def get_reports_by_date(db: AsyncSession, date_str: str) -> list[RetailReport]:
    """
    Fetch all Retail reports generated on a specific date (YYYY-MM-DD).
    """
    query = (
        select(RetailReport)
        .where(func.date(RetailReport.date) == date_str)
        .order_by(RetailReport.rank.asc(), RetailReport.ticker.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_distinct_tracked_tickers(db: AsyncSession) -> list[str]:
    """
    Fetch all distinct ticker symbols that have reports in the database across engines.
    """
    q1 = select(distinct(RetailReport.ticker))
    q2 = select(distinct(SmartMoneyReport.ticker))
    res1 = (await db.execute(q1)).scalars().all()
    res2 = (await db.execute(q2)).scalars().all()
    all_tickers = set([r for r in res1 if r] + [r for r in res2 if r])
    return sorted(list(all_tickers))


async def get_ticker_history(db: AsyncSession, ticker: str):
    """
    Fetch all historical reports for a given ticker ordered by date ascending across all engines.
    Supports Retail Momentum candidates, Smart Money Scout candidates, and Core Equity Intel records.
    """
    sym = ticker.upper()
    # 1. Check RetailReports
    query_retail = (
        select(RetailReport)
        .where(RetailReport.ticker == sym)
        .order_by(RetailReport.date.asc())
    )
    res_retail = list((await db.execute(query_retail)).scalars().all())
    if res_retail:
        return res_retail

    # 2. Check SmartMoneyReports with linked CoreEquityIntel
    query_smart = (
        select(SmartMoneyReport)
        .where(SmartMoneyReport.ticker == sym)
        .order_by(SmartMoneyReport.date.asc())
    )
    res_smart = list((await db.execute(query_smart)).scalars().all())
    if res_smart:
        history_points = []
        for sm in res_smart:
            core_intel = None
            if sm.core_intel_id:
                core_intel = await get_core_equity_intel_by_id(db, sm.core_intel_id)
            if not core_intel:
                core_intel = await get_latest_core_equity_intel(db, sym)

            curr_p = sm.current_price or (core_intel.current_price if core_intel else None)
            targ_p = sm.target_price or (core_intel.target_price if core_intel else None)
            raw_m = (core_intel.raw_metrics if core_intel else {}) or {}

            is_alpha = "Alpha" in (sm.conviction_tier or "") or "High" in (sm.conviction_tier or "")
            rec = "BUY" if is_alpha else "HOLD"

            point = SimpleNamespace(
                id=sm.id,
                ticker=sm.ticker,
                date=sm.date,
                current_price=curr_p,
                target_price=targ_p,
                community_sentiment="Stealth (Unmonitored by Retail)",
                community_hype=sm.top_buyer_summary or "Early institutional cluster accumulation detected.",
                ground_truth_status=sm.ground_truth_status or (core_intel.ground_truth_status if core_intel else "Objective financial and SEC filing evaluation."),
                reconciliation_risk_score=(core_intel.risk_score if core_intel else "Medium") or "Medium",
                reconciliation_actionable_insight=sm.actionable_thesis or (core_intel.actionable_insight if core_intel else "Track insider buying and contract horizon."),
                recommendation=rec,
                recommendation_rationale=sm.actionable_thesis or "High-conviction smart money cluster buying.",
                smart_money_verdict=sm.conviction_tier or "Tier-1 Alpha",
                raw_metrics=raw_m,
            )
            history_points.append(point)
        return history_points

    # 3. Fallback to CoreEquityIntel directly if neither overlay exists
    query_core = (
        select(CoreEquityIntel)
        .where(CoreEquityIntel.ticker == sym)
        .order_by(CoreEquityIntel.date.asc())
    )
    res_core = list((await db.execute(query_core)).scalars().all())
    if res_core:
        history_points = []
        for c in res_core:
            point = SimpleNamespace(
                id=c.id,
                ticker=c.ticker,
                date=c.date,
                current_price=c.current_price,
                target_price=c.target_price,
                community_sentiment="Fundamental Baseline",
                community_hype="Identified via market evaluation.",
                ground_truth_status=c.ground_truth_status or "Objective financial and SEC filing evaluation.",
                reconciliation_risk_score=c.risk_score or "Medium",
                reconciliation_actionable_insight=c.actionable_insight or "Monitor quarterly filings.",
                recommendation="HOLD",
                recommendation_rationale="Core equity research baseline.",
                smart_money_verdict="Neutral",
                raw_metrics=c.raw_metrics or {},
            )
            history_points.append(point)
        return history_points

    return []


async def get_latest_retail_report(db: AsyncSession, ticker: str) -> RetailReport | None:
    """Fetch the latest Retail report for a specific ticker."""
    query = (
        select(RetailReport)
        .where(RetailReport.ticker == ticker.upper())
        .order_by(desc(RetailReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ==========================================
# Trajectory Meta-Analysis CRUD
# ==========================================

async def get_cached_trajectory_analysis(db: AsyncSession, ticker: str, latest_report_id: int) -> TickerTrajectoryAnalysis | None:
    """
    Retrieve cached trajectory analysis for a ticker matching the latest report id.
    """
    query = (
        select(TickerTrajectoryAnalysis)
        .where(
            TickerTrajectoryAnalysis.ticker == ticker.upper(),
            TickerTrajectoryAnalysis.latest_report_id == latest_report_id
        )
        .order_by(desc(TickerTrajectoryAnalysis.created_at))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def save_trajectory_analysis(
    db: AsyncSession,
    ticker: str,
    latest_report_id: int,
    report_count: int,
    analysis: TrajectoryAnalysis
) -> TickerTrajectoryAnalysis:
    """
    Save generated trajectory meta-analysis to the cache table.
    """
    record = TickerTrajectoryAnalysis(
        ticker=ticker.upper(),
        latest_report_id=latest_report_id,
        report_count=report_count,
        divergence_analysis=analysis.divergence_analysis,
        catalyst_follow_through=analysis.catalyst_follow_through,
        trajectory_outlook=analysis.trajectory_outlook
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# ==========================================
# Smart Money & Political Scout CRUD
# ==========================================

async def save_smart_money_tickers(db: AsyncSession, scored_candidates: list[dict]) -> list[SmartMoneyTicker]:
    """Save the top ranked smart money tickers from Engine 2."""
    saved = []
    for idx, item in enumerate(scored_candidates):
        row = SmartMoneyTicker(
            ticker=item["ticker"].upper(),
            rank=idx + 1,
            conviction_score=item.get("conviction_score", 0.0),
            insider_score=item.get("insider_score", 0.0),
            political_score=item.get("political_score", 0.0),
            cluster_count=item.get("cluster_count", 0),
            total_buy_volume=item.get("total_buy_volume", 0.0),
            top_buyer_summary=item.get("top_buyer_summary", "")
        )
        db.add(row)
        saved.append(row)
    await db.commit()
    return saved


async def get_latest_smart_money_tickers(db: AsyncSession) -> list[SmartMoneyTicker]:
    """Retrieve the most recent run's smart money tickers."""
    latest_ts_query = select(func.max(SmartMoneyTicker.date))
    latest_ts_res = await db.execute(latest_ts_query)
    latest_ts = latest_ts_res.scalar_one_or_none()
    if not latest_ts:
        return []

    query = (
        select(SmartMoneyTicker)
        .where(SmartMoneyTicker.date >= latest_ts - timedelta(minutes=2))
        .order_by(SmartMoneyTicker.rank.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def save_smart_money_report(
    db: AsyncSession,
    report_data: dict,
    core_intel_id: int | None = None
) -> SmartMoneyReport:
    """Save an Engine 2 catalyst intelligence report linked to CoreEquityIntel."""
    row = SmartMoneyReport(
        ticker=report_data["ticker"].upper(),
        core_intel_id=core_intel_id,
        rank=report_data.get("rank"),
        company_name=report_data.get("company_name", ""),
        sector=report_data.get("sector", ""),
        industry=report_data.get("industry", ""),
        current_price=report_data.get("current_price"),
        target_price=report_data.get("target_price"),
        conviction_score=report_data.get("conviction_score", 0.0),
        conviction_tier=report_data.get("conviction_tier", "High Conviction Catalyst Buy"),
        cluster_count=report_data.get("cluster_count", 0),
        total_buy_volume=report_data.get("total_buy_volume", 0.0),
        top_buyer_summary=report_data.get("top_buyer_summary", ""),
        inflow_ledger=report_data.get("inflow_ledger", []),
        political_catalyst_analysis=report_data.get("political_catalyst_analysis", ""),
        corporate_catalyst_analysis=report_data.get("corporate_catalyst_analysis", ""),
        catalyst_horizon=report_data.get("catalyst_horizon", ""),
        actionable_thesis=report_data.get("actionable_thesis", ""),
        ground_truth_status=report_data.get("ground_truth_status"),
        ground_truth_filings_news=report_data.get("ground_truth_filings_news"),
        events_happenings=report_data.get("events_happenings"),
        risk_score=report_data.get("risk_score"),
        raw_metrics=report_data.get("raw_metrics", {})
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_latest_smart_money_report(db: AsyncSession, ticker: str) -> SmartMoneyReport | None:
    """Fetch the latest smart money catalyst report for a specific ticker."""
    query = (
        select(SmartMoneyReport)
        .where(SmartMoneyReport.ticker == ticker.upper())
        .order_by(desc(SmartMoneyReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_smart_money_reports_by_date(db: AsyncSession, date_str: str) -> list[SmartMoneyReport]:
    """Fetch all Smart Money reports generated on a specific date (YYYY-MM-DD)."""
    query = (
        select(SmartMoneyReport)
        .where(func.date(SmartMoneyReport.date) == date_str)
        .order_by(SmartMoneyReport.rank.asc(), SmartMoneyReport.conviction_score.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


# ==========================================
# Cross-Engine Synthesis CRUD
# ==========================================

async def save_synthesis_records(db: AsyncSession, records: list[dict]) -> list[SynthesisRecord]:
    """Save cross-engine synthesis archetype classifications."""
    saved = []
    for item in records:
        row = SynthesisRecord(
            ticker=item["ticker"].upper(),
            core_intel_id=item.get("core_intel_id"),
            archetype=item.get("archetype", "Market Noise"),
            retail_rank=item.get("retail_rank"),
            retail_mentions=item.get("retail_mentions", 0),
            retail_sentiment=item.get("retail_sentiment"),
            smart_money_rank=item.get("smart_money_rank"),
            smart_money_conviction=item.get("smart_money_conviction", 0.0),
            smart_money_flow=item.get("smart_money_flow"),
            retail_awareness_level=item.get("retail_awareness_level", "Zero Awareness (Stealth)"),
            timing_edge_score=item.get("timing_edge_score", 0.0),
            synthesis_diagnosis=item.get("synthesis_diagnosis", ""),
            recommended_action=item.get("recommended_action", "PASS")
        )
        db.add(row)
        saved.append(row)
    await db.commit()
    return saved


async def get_latest_synthesis_records(db: AsyncSession) -> list[SynthesisRecord]:
    """Retrieve the latest synthesis matrix records, deduplicated by ticker."""
    latest_ts_query = select(func.max(SynthesisRecord.date))
    latest_ts_res = await db.execute(latest_ts_query)
    latest_ts = latest_ts_res.scalar_one_or_none()
    if not latest_ts:
        return []

    # Fetch recent records within 15 seconds of the latest timestamp
    query = (
        select(SynthesisRecord)
        .where(SynthesisRecord.date >= latest_ts - timedelta(seconds=15))
        .order_by(SynthesisRecord.date.desc(), SynthesisRecord.timing_edge_score.desc())
    )
    result = await db.execute(query)
    records = list(result.scalars().all())

    # Ensure each ticker appears at most once (keeping newest / highest edge)
    seen_tickers = set()
    deduped = []
    for r in records:
        sym = r.ticker.upper()
        if sym not in seen_tickers:
            seen_tickers.add(sym)
            deduped.append(r)

    deduped.sort(key=lambda x: x.timing_edge_score, reverse=True)
    return deduped


async def get_synthesis_records_by_date(db: AsyncSession, date_str: str) -> list[SynthesisRecord]:
    """Retrieve synthesis matrix records for a specific date (YYYY-MM-DD), deduplicated by ticker."""
    query = (
        select(SynthesisRecord)
        .where(func.date(SynthesisRecord.date) == date_str)
        .order_by(SynthesisRecord.date.desc(), SynthesisRecord.timing_edge_score.desc())
    )
    result = await db.execute(query)
    records = list(result.scalars().all())

    seen_tickers = set()
    deduped = []
    for r in records:
        sym = r.ticker.upper()
        if sym not in seen_tickers:
            seen_tickers.add(sym)
            deduped.append(r)

    deduped.sort(key=lambda x: x.timing_edge_score, reverse=True)
    return deduped


async def get_synthesis_record_by_ticker(db: AsyncSession, ticker: str) -> SynthesisRecord | None:
    """Retrieve the latest synthesis record for a ticker."""
    query = (
        select(SynthesisRecord)
        .where(SynthesisRecord.ticker == ticker.upper())
        .order_by(desc(SynthesisRecord.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_ticker_archetype_history(db: AsyncSession, ticker: str) -> list[SynthesisRecord]:
    """Retrieve chronological synthesis archetype progression for a single ticker."""
    query = (
        select(SynthesisRecord)
        .where(SynthesisRecord.ticker == ticker.upper())
        .order_by(SynthesisRecord.date.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())
