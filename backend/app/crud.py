from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, distinct
from datetime import timedelta
from app.models import (
    DailyTicker,
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
            ticker=item["ticker"],
            rank=idx + 1,
            mention_count=item["mention_count"],
            engagement_score=item["engagement_score"]
        )
        db.add(db_ticker)
    await db.commit()

async def save_ticker_report(
    db: AsyncSession,
    ticker: str,
    report: StockReport,
    metrics: dict,
    news: list,
    insider_data: dict | None = None
):
    """
    Save the generated report and raw data to the database.
    """
    db_report = TickerReport(
        ticker=ticker,
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
    Returns a list of unique report dates formatted as YYYY-MM-DD in descending order.
    """
    date_col = func.date(TickerReport.date)
    query = select(date_col).distinct().order_by(desc(date_col))
    result = await db.execute(query)
    dates = [str(row[0]) for row in result.all() if row[0] is not None]
    return dates

async def get_reports_by_date(db: AsyncSession, date_str: str) -> list[TickerReport]:
    """
    Fetch all reports generated on a specific date (YYYY-MM-DD).
    """
    query = (
        select(TickerReport)
        .where(func.date(TickerReport.date) == date_str)
        .order_by(TickerReport.ticker)
    )
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_distinct_tracked_tickers(db: AsyncSession) -> list[str]:
    """
    Fetch all distinct ticker symbols that have reports in the database.
    """
    query = select(distinct(TickerReport.ticker)).order_by(TickerReport.ticker)
    result = await db.execute(query)
    return [row[0] for row in result.all() if row[0] is not None]

async def get_ticker_history(db: AsyncSession, ticker: str) -> list[TickerReport]:
    """
    Fetch all historical reports for a given ticker ordered by date ascending.
    """
    query = (
        select(TickerReport)
        .where(TickerReport.ticker == ticker.upper())
        .order_by(TickerReport.date.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())

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
    Persist newly generated trajectory meta-analysis to the database.
    """
    db_analysis = TickerTrajectoryAnalysis(
        ticker=ticker.upper(),
        latest_report_id=latest_report_id,
        report_count=report_count,
        divergence_analysis=analysis.divergence_analysis,
        catalyst_follow_through=analysis.catalyst_follow_through,
        trajectory_outlook=analysis.trajectory_outlook
    )
    db.add(db_analysis)
    await db.commit()
    await db.refresh(db_analysis)
    return db_analysis


# ==========================================
# Engine 2: Smart Money & Political CRUD
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


async def save_smart_money_report(db: AsyncSession, report_data: dict) -> SmartMoneyReport:
    """Save an Engine 2 catalyst intelligence report."""
    row = SmartMoneyReport(
        ticker=report_data["ticker"].upper(),
        company_name=report_data.get("company_name", ""),
        sector=report_data.get("sector", ""),
        industry=report_data.get("industry", ""),
        current_price=report_data.get("current_price"),
        target_price=report_data.get("target_price"),
        conviction_score=report_data.get("conviction_score", 0.0),
        conviction_tier=report_data.get("conviction_tier", "High Conviction Catalyst Buy"),
        inflow_ledger=report_data.get("inflow_ledger", []),
        political_catalyst_analysis=report_data.get("political_catalyst_analysis", ""),
        corporate_catalyst_analysis=report_data.get("corporate_catalyst_analysis", ""),
        catalyst_horizon=report_data.get("catalyst_horizon", ""),
        actionable_thesis=report_data.get("actionable_thesis", ""),
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


# ==========================================
# Cross-Engine Synthesis CRUD
# ==========================================

async def save_synthesis_records(db: AsyncSession, records: list[dict]) -> list[SynthesisRecord]:
    """Save cross-engine synthesis archetype classifications."""
    saved = []
    for item in records:
        row = SynthesisRecord(
            ticker=item["ticker"].upper(),
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

