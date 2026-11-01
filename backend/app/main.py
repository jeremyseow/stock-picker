from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from app.database import init_db, get_db, AsyncSessionLocal
from app.models import DailyTicker, TickerReport
from app.scheduler import setup_scheduler
from app.crud import (
    get_distinct_report_dates,
    get_reports_by_date,
    get_distinct_tracked_tickers,
    get_ticker_history,
    get_cached_trajectory_analysis,
    save_trajectory_analysis,
    get_latest_smart_money_tickers,
    get_latest_smart_money_report,
    get_latest_synthesis_records,
)
from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.smart_money_researcher import get_historical_trade_price
from app.synthesis_engine import generate_cross_engine_synthesis
from app.agent import generate_trajectory_analysis
from app.ticker_extractor import TICKER_ALIASES
from datetime import timedelta

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
    """Get the top tickers from the most recent pipeline run, along with key details from the latest report."""
    # Use the latest run rather than "today in UTC": UTC midnight is 08:00 SGT, which left the
    # dashboard empty until the 20:00 SGT run. All tickers in a run are committed together.
    latest = (await db.execute(select(func.max(DailyTicker.date)))).scalar()
    if latest is None:
        return []
    run_start = latest - timedelta(hours=1)

    query = select(DailyTicker).where(DailyTicker.date >= run_start).order_by(DailyTicker.rank)
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
            "smart_money_verdict": report.smart_money_verdict if report else None,
            "current_price": report.current_price if report else None,
            "target_price": report.target_price if report else None,
            "industry": report.raw_metrics.get("industry") if report and report.raw_metrics else "Unknown",
            "sector": report.raw_metrics.get("sector") if report and report.raw_metrics else "Unknown"
        })
        
    return combined


@app.get("/api/reports/dates")
async def get_report_dates(db: AsyncSession = Depends(get_db)):
    """Get all unique dates on which analysis reports were generated."""
    return await get_distinct_report_dates(db)


@app.get("/api/reports")
async def get_reports_by_query(
    date: str | None = Query(None, description="Report date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    """Get all reports generated on a specific date, or latest if date is omitted."""
    if not date:
        available_dates = await get_distinct_report_dates(db)
        if not available_dates:
            return []
        date = available_dates[0]

    reports = await get_reports_by_date(db, date)
    formatted = []
    for r in reports:
        formatted.append({
            "id": r.id,
            "ticker": r.ticker,
            "date": r.date,
            "current_price": r.current_price,
            "target_price": r.target_price,
            "recommendation": r.recommendation,
            "recommendation_rationale": r.recommendation_rationale,
            "smart_money_verdict": r.smart_money_verdict,
            "community_sentiment": r.community_sentiment,
            "community_hype": r.community_hype,
            "ground_truth_status": r.ground_truth_status,
            "reconciliation_risk_score": r.reconciliation_risk_score,
            "reconciliation_actionable_insight": r.reconciliation_actionable_insight,
            "industry": r.raw_metrics.get("industry") if r.raw_metrics else "Unknown",
            "sector": r.raw_metrics.get("sector") if r.raw_metrics else "Unknown",
            "raw_insider_data": r.raw_insider_data
        })
    return formatted


@app.get("/api/reports/{ticker}")
async def get_ticker_report(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest report for a specific ticker."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    query = select(TickerReport).where(TickerReport.ticker == ticker).order_by(desc(TickerReport.date)).limit(1)
    result = await db.execute(query)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return report

@app.get("/api/reports/{ticker}/text", response_class=PlainTextResponse)
async def get_ticker_report_text(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest report for a specific ticker formatted as plain text."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
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

@app.get("/api/analytics/tickers")
async def get_analytics_tickers(db: AsyncSession = Depends(get_db)):
    """Get list of all tickers that have at least one persisted report."""
    return await get_distinct_tracked_tickers(db)


@app.get("/api/analytics/ticker/{ticker}")
async def get_ticker_analytics(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get historical time-series report data for a specific ticker."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    history = await get_ticker_history(db, ticker)
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical reports found for ticker {ticker.upper()}")

    results = []
    for r in history:
        results.append({
            "id": r.id,
            "ticker": r.ticker,
            "date": r.date.isoformat(),
            "current_price": r.current_price,
            "target_price": r.target_price,
            "community_sentiment": r.community_sentiment,
            "community_hype": r.community_hype,
            "ground_truth_status": r.ground_truth_status,
            "reconciliation_risk_score": r.reconciliation_risk_score,
            "reconciliation_actionable_insight": r.reconciliation_actionable_insight,
            "recommendation": r.recommendation,
            "recommendation_rationale": r.recommendation_rationale,
            "smart_money_verdict": r.smart_money_verdict,
            "raw_metrics": r.raw_metrics
        })
    return results


@app.get("/api/analytics/ticker/{ticker}/meta-analysis")
async def get_ticker_meta_analysis(ticker: str, db: AsyncSession = Depends(get_db)):
    """Fetch cached trajectory meta-analysis if available."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    history = await get_ticker_history(db, ticker)
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical reports found for ticker {ticker.upper()}")
    
    latest_report_id = history[-1].id
    cached = await get_cached_trajectory_analysis(db, ticker, latest_report_id)
    if not cached:
        return {
            "cached": False,
            "analysis": None,
            "report_count": len(history),
            "can_generate": len(history) >= 2
        }
    
    return {
        "cached": True,
        "analysis": {
            "id": cached.id,
            "ticker": cached.ticker,
            "created_at": cached.created_at.isoformat(),
            "latest_report_id": cached.latest_report_id,
            "report_count": cached.report_count,
            "divergence_analysis": cached.divergence_analysis,
            "catalyst_follow_through": cached.catalyst_follow_through,
            "trajectory_outlook": cached.trajectory_outlook
        },
        "report_count": len(history),
        "can_generate": len(history) >= 2
    }


@app.post("/api/analytics/ticker/{ticker}/meta-analysis")
async def generate_or_refresh_ticker_meta_analysis(
    ticker: str,
    force_refresh: bool = Query(False, description="Force re-generation even if cached"),
    db: AsyncSession = Depends(get_db)
):
    """Generate or retrieve cached AI trajectory meta-analysis for a ticker across all runs."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    history = await get_ticker_history(db, ticker)
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical reports found for ticker {ticker.upper()}")

    if len(history) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"At least 2 historical reports are required to generate trajectory meta-analysis. {ticker.upper()} has {len(history)}."
        )

    latest_report = history[-1]
    latest_report_id = latest_report.id

    if not force_refresh:
        cached = await get_cached_trajectory_analysis(db, ticker, latest_report_id)
        if cached:
            return {
                "cached": True,
                "analysis": {
                    "id": cached.id,
                    "ticker": cached.ticker,
                    "created_at": cached.created_at.isoformat(),
                    "latest_report_id": cached.latest_report_id,
                    "report_count": cached.report_count,
                    "divergence_analysis": cached.divergence_analysis,
                    "catalyst_follow_through": cached.catalyst_follow_through,
                    "trajectory_outlook": cached.trajectory_outlook
                }
            }

    # Format history payload for Gemini agent
    formatted_reports = []
    for r in history:
        formatted_reports.append({
            "date": r.date.strftime("%Y-%m-%d"),
            "current_price": r.current_price,
            "target_price": r.target_price,
            "recommendation": r.recommendation,
            "recommendation_rationale": r.recommendation_rationale,
            "smart_money_verdict": r.smart_money_verdict,
            "community_sentiment": r.community_sentiment,
            "community_hype": r.community_hype,
            "reconciliation_risk_score": r.reconciliation_risk_score,
            "ground_truth_status": r.ground_truth_status,
            "reconciliation_actionable_insight": r.reconciliation_actionable_insight
        })

    analysis = await generate_trajectory_analysis(ticker.upper(), formatted_reports)
    saved = await save_trajectory_analysis(db, ticker.upper(), latest_report_id, len(history), analysis)

    return {
        "cached": False,
        "analysis": {
            "id": saved.id,
            "ticker": saved.ticker,
            "created_at": saved.created_at.isoformat(),
            "latest_report_id": saved.latest_report_id,
            "report_count": saved.report_count,
            "divergence_analysis": saved.divergence_analysis,
            "catalyst_follow_through": saved.catalyst_follow_through,
            "trajectory_outlook": saved.trajectory_outlook
        }
    }


@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get some basic statistics."""
    # For MVP, just return the most mentioned tickers of all time
    query = select(DailyTicker).order_by(desc(DailyTicker.mention_count)).limit(10)
    result = await db.execute(query)
    tickers = result.scalars().all()
    return tickers


# ==========================================
# Engine 2: Smart Money & Political Endpoints
# ==========================================

@app.get("/api/smart-money/today")
async def get_today_smart_money(db: AsyncSession = Depends(get_db)):
    """Fetch the latest Smart Money & Political Scout candidate tickers."""
    tickers = await get_latest_smart_money_tickers(db)
    results = []
    for t in tickers:
        report = await get_latest_smart_money_report(db, t.ticker)
        results.append({
            "id": t.id,
            "date": t.date.isoformat(),
            "ticker": t.ticker,
            "rank": t.rank,
            "conviction_score": t.conviction_score,
            "insider_score": t.insider_score,
            "political_score": t.political_score,
            "cluster_count": t.cluster_count,
            "total_buy_volume": t.total_buy_volume,
            "top_buyer_summary": t.top_buyer_summary,
            "conviction_tier": report.conviction_tier if report else "High Conviction Catalyst Buy",
            "sector": report.sector if report else "General",
            "industry": report.industry if report else "General",
            "current_price": report.current_price if report else None,
            "target_price": report.target_price if report else None,
        })
    return results


@app.get("/api/smart-money/report/{ticker}")
async def get_smart_money_report_detail(ticker: str, db: AsyncSession = Depends(get_db)):
    """Fetch detailed smart money catalyst report and inflow ledger."""
    rep = await get_latest_smart_money_report(db, ticker.upper())
    if not rep:
        raise HTTPException(status_code=404, detail=f"No smart money report found for ${ticker.upper()}")
    
    inflow_ledger = []
    for item in (rep.inflow_ledger or []):
        entry = dict(item)
        if not entry.get("price") or entry.get("price") == "N/A":
            t_date = entry.get("date")
            p = get_historical_trade_price(rep.ticker, t_date) if t_date else None
            if p:
                entry["price"] = f"${p:.2f}"
            elif rep.current_price:
                entry["price"] = f"~${rep.current_price:.2f}"
            else:
                entry["price"] = "Market"
        inflow_ledger.append(entry)

    return {
        "id": rep.id,
        "ticker": rep.ticker,
        "date": rep.date.isoformat(),
        "company_name": rep.company_name,
        "sector": rep.sector,
        "industry": rep.industry,
        "current_price": rep.current_price,
        "target_price": rep.target_price,
        "conviction_score": rep.conviction_score,
        "conviction_tier": rep.conviction_tier,
        "inflow_ledger": inflow_ledger,
        "political_catalyst_analysis": rep.political_catalyst_analysis,
        "corporate_catalyst_analysis": rep.corporate_catalyst_analysis,
        "catalyst_horizon": rep.catalyst_horizon,
        "actionable_thesis": rep.actionable_thesis,
        "raw_metrics": rep.raw_metrics,
    }


# ==========================================
# Cross-Engine Synthesis Endpoints
# ==========================================

@app.get("/api/synthesis/today")
async def get_today_synthesis(db: AsyncSession = Depends(get_db)):
    """Fetch the latest cross-engine archetype synthesis matrix records."""
    records = await get_latest_synthesis_records(db)
    return [
        {
            "id": r.id,
            "ticker": r.ticker,
            "date": r.date.isoformat(),
            "archetype": r.archetype,
            "retail_rank": r.retail_rank,
            "retail_mentions": r.retail_mentions,
            "retail_sentiment": r.retail_sentiment,
            "smart_money_rank": r.smart_money_rank,
            "smart_money_conviction": r.smart_money_conviction,
            "smart_money_flow": r.smart_money_flow,
            "retail_awareness_level": r.retail_awareness_level,
            "timing_edge_score": r.timing_edge_score,
            "synthesis_diagnosis": r.synthesis_diagnosis,
            "recommended_action": r.recommended_action,
        }
        for r in records
    ]


@app.post("/api/pipeline/trigger")
async def trigger_retail_pipeline():
    """Triggers an on-demand execution of Engine 1 (Retail Momentum) and refreshes Cross-Engine Synthesis."""
    logger.info("Manual trigger received for Engine 1 (Retail Momentum)...")
    await run_analysis_pipeline()
    try:
        async with AsyncSessionLocal() as db:
            await generate_cross_engine_synthesis(db)
    except Exception as e:
        logger.warning(f"Could not refresh cross-engine synthesis after Engine 1: {e}")
    return {"status": "success"}


@app.post("/api/smart-money/trigger")
async def trigger_smart_money_run():
    """Triggers an on-demand execution of Engine 2 and refreshes Cross-Engine Synthesis."""
    logger.info("Manual trigger received for Engine 2 (Smart Money Scout)...")
    reports = await run_smart_money_pipeline(limit=5)
    try:
        async with AsyncSessionLocal() as db:
            await generate_cross_engine_synthesis(db)
    except Exception as e:
        logger.warning(f"Could not refresh cross-engine synthesis after Engine 2: {e}")
    return {
        "status": "success",
        "smart_money_reports_count": len(reports),
    }

