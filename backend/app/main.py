from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func

from app.database import init_db, get_db, AsyncSessionLocal
from app.models import DailyTicker, RetailReport
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
    get_smart_money_reports_by_date,
    get_latest_synthesis_records,
    get_synthesis_records_by_date,
    get_synthesis_record_by_ticker,
    get_ticker_archetype_history,
    get_latest_core_equity_intel,
    get_latest_retail_report,
    get_latest_options_whale_tickers,
    get_latest_options_whale_report,
    get_options_reports_by_date,
    get_latest_model_calibration_run,
)
from app.options_pipeline import run_options_pipeline
from app.backtest_engine import run_walk_forward_backtest
from app.scoring_weights import get_active_weights, update_active_weights
from app.pipeline import run_analysis_pipeline
from app.smart_money_pipeline import run_smart_money_pipeline
from app.smart_money_researcher import get_historical_trade_price
from app.synthesis_engine import generate_cross_engine_synthesis
from app.agent import generate_trajectory_analysis
from app.ticker_extractor import TICKER_ALIASES
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

@app.get("/api/retail/today")
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
        report_query = select(RetailReport).where(RetailReport.ticker == t.ticker).order_by(desc(RetailReport.date)).limit(1)
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


@app.get("/api/dates")
async def get_report_dates(db: AsyncSession = Depends(get_db)):
    """Get all unique dates on which analysis reports were generated."""
    return await get_distinct_report_dates(db)


@app.get("/api/retail/reports")
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


@app.get("/api/retail/report/{ticker}")
async def get_retail_report_detail(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get detailed retail momentum report for a ticker, including linked core equity intel."""
    ticker_sym = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    retail_rep = await get_latest_retail_report(db, ticker_sym)
    if not retail_rep:
        raise HTTPException(status_code=404, detail=f"No retail report found for ${ticker_sym}")
    core_intel = await get_latest_core_equity_intel(db, ticker_sym)

    return {
        "id": retail_rep.id,
        "ticker": retail_rep.ticker,
        "date": retail_rep.date.isoformat(),
        "rank": retail_rep.rank,
        "current_price": retail_rep.current_price,
        "target_price": retail_rep.target_price,
        "recommendation": retail_rep.recommendation,
        "recommendation_rationale": retail_rep.recommendation_rationale,
        "community_sentiment": retail_rep.community_sentiment,
        "community_hype": retail_rep.community_hype,
        "ground_truth_status": retail_rep.ground_truth_status,
        "ground_truth_filings_news": retail_rep.ground_truth_filings_news,
        "events_happenings": retail_rep.events_happenings,
        "reconciliation_risk_score": retail_rep.reconciliation_risk_score,
        "reconciliation_analysis": retail_rep.reconciliation_analysis,
        "reconciliation_actionable_insight": retail_rep.reconciliation_actionable_insight,
        "raw_metrics": retail_rep.raw_metrics,
        "raw_news": retail_rep.raw_news,
        "raw_insider_data": retail_rep.raw_insider_data,
        "core_intel": {
            "has_data": core_intel is not None,
            "company_name": core_intel.company_name if core_intel else retail_rep.ticker,
            "sector": core_intel.sector if core_intel else "General",
            "industry": core_intel.industry if core_intel else "General",
            "raw_metrics": core_intel.raw_metrics if core_intel else retail_rep.raw_metrics,
        }
    }


@app.get("/api/master/report/{ticker}")
async def get_ticker_report(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the unified master report for a specific ticker across all engines."""
    ticker_sym = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    core_intel = await get_latest_core_equity_intel(db, ticker_sym)
    retail_rep = await get_latest_retail_report(db, ticker_sym)
    smart_money_rep = await get_latest_smart_money_report(db, ticker_sym)
    synthesis_rec = await get_synthesis_record_by_ticker(db, ticker_sym)

    if not core_intel and not retail_rep and not smart_money_rep:
        raise HTTPException(status_code=404, detail=f"Report for ${ticker_sym} not found")

    company_name = (core_intel and core_intel.company_name) or (smart_money_rep and smart_money_rep.company_name) or ticker_sym
    sector = (core_intel and core_intel.sector) or (smart_money_rep and smart_money_rep.sector) or "General"
    industry = (core_intel and core_intel.industry) or (smart_money_rep and smart_money_rep.industry) or "General"
    current_price = (core_intel and core_intel.current_price) or (retail_rep and retail_rep.current_price) or (smart_money_rep and smart_money_rep.current_price)
    target_price = (core_intel and core_intel.target_price) or (retail_rep and retail_rep.target_price) or (smart_money_rep and smart_money_rep.target_price)
    raw_metrics = (core_intel and core_intel.raw_metrics) or (retail_rep and retail_rep.raw_metrics) or (smart_money_rep and smart_money_rep.raw_metrics) or {}

    inflow_ledger = []
    if smart_money_rep and smart_money_rep.inflow_ledger:
        for item in smart_money_rep.inflow_ledger:
            entry = dict(item)
            if not entry.get("price") or entry.get("price") == "N/A":
                t_date = entry.get("date")
                p = get_historical_trade_price(ticker_sym, t_date) if t_date else None
                if p:
                    entry["price"] = f"${p:.2f}"
                elif current_price:
                    entry["price"] = f"~${current_price:.2f}"
                else:
                    entry["price"] = "Market"
            inflow_ledger.append(entry)

    # Calculate potential upside
    potential_upside = None
    if current_price and target_price and current_price > 0:
        potential_upside = ((target_price - current_price) / current_price) * 100

    report_date = (core_intel and core_intel.date) or (retail_rep and retail_rep.date) or (smart_money_rep and smart_money_rep.date)

    return {
        "id": (retail_rep and retail_rep.id) or (smart_money_rep and smart_money_rep.id) or (core_intel and core_intel.id),
        "ticker": ticker_sym,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "current_price": current_price,
        "target_price": target_price,
        "potential_upside": potential_upside,
        "date": report_date.isoformat() if report_date else None,

        # Top-level backward compatibility fields
        "ground_truth_status": (core_intel and core_intel.ground_truth_status) or (retail_rep and retail_rep.ground_truth_status) or (smart_money_rep and smart_money_rep.ground_truth_status),
        "ground_truth_filings_news": (core_intel and core_intel.ground_truth_filings_news) or (retail_rep and retail_rep.ground_truth_filings_news) or (smart_money_rep and smart_money_rep.ground_truth_filings_news),
        "events_happenings": (core_intel and core_intel.events_happenings) or (retail_rep and retail_rep.events_happenings) or (smart_money_rep and smart_money_rep.events_happenings),
        "reconciliation_risk_score": (core_intel and core_intel.risk_score) or (retail_rep and retail_rep.reconciliation_risk_score) or (smart_money_rep and smart_money_rep.risk_score) or "Medium",
        "reconciliation_analysis": (core_intel and core_intel.risk_analysis) or (retail_rep and retail_rep.reconciliation_analysis),
        "reconciliation_actionable_insight": (core_intel and core_intel.actionable_insight) or (retail_rep and retail_rep.reconciliation_actionable_insight) or (smart_money_rep and smart_money_rep.actionable_thesis),
        "recommendation": retail_rep.recommendation if retail_rep else "HOLD",
        "recommendation_rationale": retail_rep.recommendation_rationale if retail_rep else "Report generated from institutional and fundamental scan.",
        "community_sentiment": retail_rep.community_sentiment if retail_rep else "Unmonitored",
        "community_hype": retail_rep.community_hype if retail_rep else "No active Reddit discussion tracked.",
        "smart_money_verdict": (retail_rep and retail_rep.smart_money_verdict) or (synthesis_rec and synthesis_rec.smart_money_flow) or (smart_money_rep and smart_money_rep.conviction_tier) or "Neutral",
        "raw_insider_data": (retail_rep and retail_rep.raw_insider_data) or {"has_data": bool(smart_money_rep), "insider_activity_summary": smart_money_rep.actionable_thesis if smart_money_rep else None, "congressional_trades": []},
        "raw_metrics": raw_metrics,
        "raw_news": (core_intel and core_intel.raw_news) or (retail_rep and retail_rep.raw_news) or [],

        # Modular Overlay Facets
        "retail_overlay": {
            "has_data": retail_rep is not None,
            "rank": retail_rep.rank if retail_rep else None,
            "mention_count": retail_rep.mention_count if retail_rep else 0,
            "community_sentiment": retail_rep.community_sentiment if retail_rep else "Unmonitored",
            "community_hype": retail_rep.community_hype if retail_rep else "No active Reddit discussion tracked.",
            "recommendation": retail_rep.recommendation if retail_rep else None,
            "recommendation_rationale": retail_rep.recommendation_rationale if retail_rep else None,
        },
        "smart_money_overlay": {
            "has_data": smart_money_rep is not None,
            "rank": smart_money_rep.rank if smart_money_rep else None,
            "conviction_score": smart_money_rep.conviction_score if smart_money_rep else 0.0,
            "conviction_tier": smart_money_rep.conviction_tier if smart_money_rep else "No Cluster",
            "cluster_count": smart_money_rep.cluster_count if smart_money_rep else 0,
            "total_buy_volume": smart_money_rep.total_buy_volume if smart_money_rep else 0.0,
            "top_buyer_summary": smart_money_rep.top_buyer_summary if smart_money_rep else None,
            "inflow_ledger": inflow_ledger,
            "political_catalyst_analysis": smart_money_rep.political_catalyst_analysis if smart_money_rep else None,
            "corporate_catalyst_analysis": smart_money_rep.corporate_catalyst_analysis if smart_money_rep else None,
            "catalyst_horizon": smart_money_rep.catalyst_horizon if smart_money_rep else None,
            "actionable_thesis": smart_money_rep.actionable_thesis if smart_money_rep else None,
        },
        "synthesis": {
            "has_data": synthesis_rec is not None,
            "archetype": synthesis_rec.archetype if synthesis_rec else "Market Noise",
            "retail_awareness_level": synthesis_rec.retail_awareness_level if synthesis_rec else "Zero Awareness (Stealth)",
            "timing_edge_score": synthesis_rec.timing_edge_score if synthesis_rec else 0.0,
            "synthesis_diagnosis": synthesis_rec.synthesis_diagnosis if synthesis_rec else None,
            "recommended_action": synthesis_rec.recommended_action if synthesis_rec else "PASS",
        }
    }

@app.get("/api/master/report/{ticker}/text", response_class=PlainTextResponse)
async def get_ticker_report_text(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest report for a specific ticker formatted as plain text."""
    ticker = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    query = select(RetailReport).where(RetailReport.ticker == ticker).order_by(desc(RetailReport.date)).limit(1)
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


@app.get("/api/analytics/ticker/{ticker}/archetypes")
async def get_ticker_archetype_progression(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get chronological synthesis archetype lifecycle progression for a ticker."""
    ticker_sym = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    history = await get_ticker_archetype_history(db, ticker_sym)
    return [
        {
            "id": r.id,
            "date": r.date.isoformat(),
            "archetype": r.archetype,
            "timing_edge_score": r.timing_edge_score,
            "retail_awareness_level": r.retail_awareness_level,
            "retail_mentions": r.retail_mentions,
            "smart_money_conviction": r.smart_money_conviction,
            "synthesis_diagnosis": r.synthesis_diagnosis,
            "recommended_action": r.recommended_action,
        }
        for r in history
    ]


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

@app.get("/api/smart-money/reports")
async def get_smart_money_reports_by_query(
    date: str | None = Query(None, description="Report date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    """Fetch Smart Money reports for a specific date, or latest available date if omitted."""
    if not date:
        available_dates = await get_distinct_report_dates(db)
        if not available_dates:
            return []
        date = available_dates[0]

    reports = await get_smart_money_reports_by_date(db, date)
    results = []
    for rep in reports:
        results.append({
            "id": rep.id,
            "ticker": rep.ticker,
            "date": rep.date.isoformat(),
            "rank": rep.rank,
            "company_name": rep.company_name,
            "sector": rep.sector,
            "industry": rep.industry,
            "current_price": rep.current_price,
            "target_price": rep.target_price,
            "conviction_score": rep.conviction_score,
            "conviction_tier": rep.conviction_tier,
            "cluster_count": rep.cluster_count,
            "total_buy_volume": rep.total_buy_volume,
            "top_buyer_summary": rep.top_buyer_summary,
            "catalyst_horizon": rep.catalyst_horizon,
            "actionable_thesis": rep.actionable_thesis,
            "political_catalyst_analysis": rep.political_catalyst_analysis,
            "corporate_catalyst_analysis": rep.corporate_catalyst_analysis,
            "ground_truth_status": rep.ground_truth_status,
            "risk_score": rep.risk_score,
            "raw_metrics": rep.raw_metrics,
        })
    return results


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
    """Fetch detailed smart money catalyst report, inflow ledger, and linked core equity intelligence."""
    ticker_sym = TICKER_ALIASES.get(ticker.upper(), ticker.upper())
    rep = await get_latest_smart_money_report(db, ticker_sym)
    if not rep:
        raise HTTPException(status_code=404, detail=f"No smart money report found for ${ticker_sym}")
    
    core_intel = await get_latest_core_equity_intel(db, ticker_sym)

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

    company_name = (core_intel and core_intel.company_name) or rep.company_name
    sector = (core_intel and core_intel.sector) or rep.sector
    industry = (core_intel and core_intel.industry) or rep.industry
    current_price = (core_intel and core_intel.current_price) or rep.current_price
    target_price = (core_intel and core_intel.target_price) or rep.target_price
    raw_metrics = (core_intel and core_intel.raw_metrics) or rep.raw_metrics or {}
    ground_truth_status = (core_intel and core_intel.ground_truth_status) or rep.ground_truth_status or "Verified"
    risk_score = (core_intel and core_intel.risk_score) or rep.risk_score or "Medium"

    return {
        "id": rep.id,
        "ticker": rep.ticker,
        "date": rep.date.isoformat(),
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "current_price": current_price,
        "target_price": target_price,
        "conviction_score": rep.conviction_score,
        "conviction_tier": rep.conviction_tier,
        "inflow_ledger": inflow_ledger,
        "political_catalyst_analysis": rep.political_catalyst_analysis,
        "corporate_catalyst_analysis": rep.corporate_catalyst_analysis,
        "catalyst_horizon": rep.catalyst_horizon,
        "actionable_thesis": rep.actionable_thesis,
        "ground_truth_status": ground_truth_status,
        "risk_score": risk_score,
        "raw_metrics": raw_metrics,
        "core_intel": {
            "has_data": core_intel is not None,
            "company_name": company_name,
            "sector": sector,
            "industry": industry,
            "current_price": current_price,
            "target_price": target_price,
            "ground_truth_status": ground_truth_status,
            "ground_truth_filings_news": (core_intel and core_intel.ground_truth_filings_news) or "SEC disclosures and corporate fundamentals verified.",
            "events_happenings": (core_intel and core_intel.events_happenings) or "Corporate filings, insider disclosures, and committee actions tracked.",
            "risk_score": risk_score,
            "risk_analysis": (core_intel and core_intel.risk_analysis) or "Fundamental risk evaluated through verified financial health and governance metrics.",
            "actionable_insight": (core_intel and core_intel.actionable_insight) or rep.actionable_thesis,
            "raw_metrics": raw_metrics,
            "raw_news": (core_intel and core_intel.raw_news) or [],
        }
    }


# ==========================================
# Cross-Engine Synthesis Endpoints
# ==========================================

@app.get("/api/synthesis/reports")
async def get_synthesis_reports_by_query(
    date: str | None = Query(None, description="Report date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db)
):
    """Fetch Synthesis Matrix records for a specific date, or latest available date if omitted."""
    if not date:
        available_dates = await get_distinct_report_dates(db)
        if not available_dates:
            return []
        date = available_dates[0]

    records = await get_synthesis_records_by_date(db, date)
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


@app.post("/api/retail/trigger")
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


# ==========================================
# Engine 3: Institutional Whale Options Endpoints
# ==========================================

@app.get("/api/options/today")
async def get_options_today(db: AsyncSession = Depends(get_db)):
    """Returns the top ranked options whale tickers from the latest run."""
    tickers = await get_latest_options_whale_tickers(db)
    return [
        {
            "id": t.id,
            "ticker": t.ticker,
            "rank": t.rank,
            "date": t.date.isoformat(),
            "whale_score": t.whale_score,
            "unusual_oi_multiplier": t.unusual_oi_multiplier,
            "net_bullish_premium": t.net_bullish_premium,
            "put_call_ratio": t.put_call_ratio,
            "top_strike_summary": t.top_strike_summary,
        }
        for t in tickers
    ]


@app.get("/api/options/reports")
async def get_options_reports(date: str = Query(..., description="Target date in YYYY-MM-DD format"), db: AsyncSession = Depends(get_db)):
    """Returns options whale reports generated on a specific historical date."""
    reports = await get_options_reports_by_date(db, date)
    return [
        {
            "id": r.id,
            "ticker": r.ticker,
            "company_name": r.company_name,
            "sector": r.sector,
            "industry": r.industry,
            "current_price": r.current_price,
            "target_price": r.target_price,
            "date": r.date.isoformat(),
            "rank": r.rank,
            "whale_score": r.whale_score,
            "unusual_oi_multiplier": r.unusual_oi_multiplier,
            "put_call_ratio": r.put_call_ratio,
            "net_bullish_premium": r.net_bullish_premium,
            "sentiment_bias": r.sentiment_bias,
            "top_strike_summary": r.top_strike_summary,
            "unusual_contracts": r.unusual_contracts or [],
            "ground_truth_status": r.ground_truth_status,
            "risk_score": r.risk_score,
        }
        for r in reports
    ]


@app.get("/api/options/report/{ticker}")
async def get_individual_options_report(ticker: str, db: AsyncSession = Depends(get_db)):
    """Returns the detailed options flow report for a specific ticker."""
    rep = await get_latest_options_whale_report(db, ticker)
    core = await get_latest_core_equity_intel(db, ticker)

    if not rep and not core:
        raise HTTPException(status_code=404, detail=f"No options flow data found for ${ticker.upper()}")

    curr_p = (rep.current_price if rep else None) or (core.current_price if core else None)
    targ_p = (rep.target_price if rep else None) or (core.target_price if core else None)

    return {
        "ticker": ticker.upper(),
        "company_name": (rep.company_name if rep else None) or (core.company_name if core else ticker.upper()),
        "sector": (rep.sector if rep else None) or (core.sector if core else None),
        "industry": (rep.industry if rep else None) or (core.industry if core else None),
        "current_price": curr_p,
        "target_price": targ_p,
        "date": rep.date.isoformat() if rep else (core.date.isoformat() if core else None),
        "rank": rep.rank if rep else None,
        "whale_score": rep.whale_score if rep else 0.0,
        "unusual_oi_multiplier": rep.unusual_oi_multiplier if rep else 1.0,
        "put_call_ratio": rep.put_call_ratio if rep else 1.0,
        "net_bullish_premium": rep.net_bullish_premium if rep else 0.0,
        "sentiment_bias": rep.sentiment_bias if rep else "Neutral Tape",
        "top_strike_summary": rep.top_strike_summary if rep else "Standard options volume",
        "unusual_contracts": rep.unusual_contracts if rep else [],
        "ground_truth_status": (rep.ground_truth_status if rep else None) or (core.ground_truth_status if core else None),
        "ground_truth_filings_news": (rep.ground_truth_filings_news if rep else None) or (core.ground_truth_filings_news if core else None),
        "events_happenings": (rep.events_happenings if rep else None) or (core.events_happenings if core else None),
        "risk_score": (rep.risk_score if rep else None) or (core.risk_score if core else "Medium"),
        "raw_metrics": (rep.raw_metrics if rep else None) or (core.raw_metrics if core else {}),
    }


@app.post("/api/options/trigger")
async def trigger_options_run():
    """Triggers an on-demand execution of Engine 3 and refreshes Cross-Engine Synthesis."""
    logger.info("Manual trigger received for Engine 3 (Whale Options Radar)...")
    reports = await run_options_pipeline(limit=5)
    try:
        async with AsyncSessionLocal() as db:
            await generate_cross_engine_synthesis(db)
    except Exception as e:
        logger.warning(f"Could not refresh cross-engine synthesis after Engine 3: {e}")
    return {
        "status": "success",
        "options_reports_count": len(reports),
    }


# ==========================================
# Model Calibration & Backtesting Endpoints
# ==========================================

@app.get("/api/calibration/scorecard")
async def get_calibration_scorecard(db: AsyncSession = Depends(get_db)):
    """Returns the performance scorecard, active weights, and recommended calibrated weights."""
    scorecard = await run_walk_forward_backtest(db)
    return scorecard


@app.post("/api/calibration/apply-weights")
async def apply_calibrated_weights(payload: dict = None, db: AsyncSession = Depends(get_db)):
    """
    Applies recommended or submitted calibrated weights to production configuration.
    """
    if payload and "weights" in payload:
        new_w = payload["weights"]
    else:
        # Run backtest to compute latest recommended weights
        backtest_res = await run_walk_forward_backtest(db)
        new_w = backtest_res["recommended_weights"]

    updated = update_active_weights(new_w)
    return {
        "status": "success",
        "message": "Calibrated parameter weights successfully applied to production.",
        "active_weights": updated,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }


