from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DailyTicker, TickerReport
from app.llm_schemas import StockReport
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
