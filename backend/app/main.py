from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.database import init_db, get_db
from app.models import DailyTicker, TickerReport
from app.scheduler import setup_scheduler
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = setup_scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB
    await init_db()
    logger.info("Database initialized.")
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started.")
    
    yield
    
    # Shutdown scheduler
    scheduler.shutdown()
    logger.info("Scheduler stopped.")

app = FastAPI(title="Subreddit Stock Analyzer API", lifespan=lifespan)

# Add CORS middleware for frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/tickers/today")
async def get_todays_tickers(db: AsyncSession = Depends(get_db)):
    """Get the top tickers extracted today, along with key details from the latest report."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    query = select(DailyTicker).where(DailyTicker.date >= today_start).order_by(DailyTicker.rank)
    result = await db.execute(query)
    tickers = result.scalars().all()
    
    combined = []
    for t in tickers:
        # Fetch the latest report for this ticker
        report_query = select(TickerReport).where(TickerReport.ticker == t.ticker).order_by(desc(TickerReport.date)).limit(1)
        report_res = await db.execute(report_query)
        report = report_res.scalar_one_or_none()
        
        combined.append({
            "id": t.id,
            "ticker": t.ticker,
            "rank": t.rank,
            "mention_count": t.mention_count,
            "engagement_score": t.engagement_score,
            "date": t.date,
            "recommendation": report.recommendation if report else None,
            "current_price": report.current_price if report else None,
            "target_price": report.target_price if report else None,
            "industry": report.raw_metrics.get("industry") if report and report.raw_metrics else "Unknown",
            "sector": report.raw_metrics.get("sector") if report and report.raw_metrics else "Unknown"
        })
        
    return combined


@app.get("/api/reports/{ticker}")
async def get_ticker_report(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest report for a specific ticker."""
    query = select(TickerReport).where(TickerReport.ticker == ticker).order_by(desc(TickerReport.date)).limit(1)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return report

@app.get("/api/reports/{ticker}/text", response_class=PlainTextResponse)
async def get_ticker_report_text(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest report for a specific ticker formatted as plain text."""
    query = select(TickerReport).where(TickerReport.ticker == ticker).order_by(desc(TickerReport.date)).limit(1)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    formatted_date = report.date.strftime("%Y-%m-%d")
    
    current_price_str = f"${report.current_price:.2f}" if report.current_price is not None else "N/A"
    target_price_str = f"${report.target_price:.2f}" if report.target_price is not None else "N/A"
    
    report_text = f"""Market Intelligence Report: {report.ticker}
Date: {formatted_date}
Price: {current_price_str} | Target: {target_price_str}

[COMMUNITY SENTIMENT]
- Sentiment: {report.community_sentiment}
- Hype: {report.community_hype}

[GROUND TRUTH]
- Status: {report.ground_truth_status}
- Filings/News: {report.ground_truth_filings_news}

[EVENTS & HAPPENINGS]
- Key Events: {report.events_happenings}

[RECONCILIATION]
- Risk Score: {report.reconciliation_risk_score}
- Analysis: {report.reconciliation_analysis}
- Actionable Insight: {report.reconciliation_actionable_insight}"""

    return report_text

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get some basic statistics."""
    # For MVP, just return the most mentioned tickers of all time
    query = select(DailyTicker).order_by(desc(DailyTicker.mention_count)).limit(10)
    result = await db.execute(query)
    tickers = result.scalars().all()
    return tickers
