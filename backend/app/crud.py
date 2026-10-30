from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, distinct
from app.models import DailyTicker, TickerReport, TickerTrajectoryAnalysis
from app.llm_schemas import StockReport, TrajectoryAnalysis
import json

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

async def save_ticker_report(db: AsyncSession, ticker: str, report: StockReport, metrics: dict, news: list):
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
