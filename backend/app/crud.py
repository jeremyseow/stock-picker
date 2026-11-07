from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, distinct
from app.models import (
    DailyTicker,
    SmartMoneyTicker,
    OptionsWhaleTicker,
    CoreEquityReport,
    RetailSentimentReport,
    SmartMoneyReport,
    OptionsWhaleReport,
    SynthesisReport,
    TickerTrajectoryAnalysis,
    ModelCalibrationRun,
    CoreEquityRaw,
    RetailSocialRaw,
    InsiderTradesRaw,
    CongressTradesRaw,
    OptionsWhaleRaw,
)
from app.llm_schemas import StockReport, TrajectoryAnalysis


async def save_retail_social_raw(db: AsyncSession, raw_social_items: list[dict]):
    """Save raw social signals and Reddit discussions to retail_social_raw."""
    for item in raw_social_items:
        sym = item["ticker"].upper()
        raw_social = RetailSocialRaw(
            ticker=sym,
            platform=item.get("platform", "reddit"),
            post_id=item.get("post_id"),
            subreddit=item.get("subreddit", "wallstreetbets,stocks"),
            title=item.get("title") or item.get("post_title") or f"Reddit discussions for {sym}",
            author=item.get("author"),
            score=int(item.get("score") or item.get("engagement_score") or 0),
            comment_count=int(item.get("comment_count") or item.get("mention_count") or 0),
            post_url=item.get("post_url"),
            post_body=item.get("post_body") or item.get("context_text"),
        )
        db.add(raw_social)
    await db.commit()


async def save_daily_tickers(db: AsyncSession, tickers: list[dict]) -> list[DailyTicker]:
    """Save the top ranked retail tickers from Engine 1 to daily_tickers."""
    saved = []
    for idx, item in enumerate(tickers):
        sym = item["ticker"].upper()
        db_ticker = DailyTicker(
            ticker=sym,
            rank=idx + 1,
            mention_count=item.get("mention_count", 0),
            engagement_score=item.get("engagement_score", 0.0)
        )
        db.add(db_ticker)
        saved.append(db_ticker)
    await db.commit()
    return saved


# ==========================================
# Core Equity Intel CRUD
# ==========================================

async def save_core_equity_report(db: AsyncSession, intel_data: dict) -> CoreEquityReport:
    """Save foundational equity intelligence and raw evidence for a ticker."""
    raw_row = CoreEquityRaw(
        ticker=intel_data["ticker"].upper(),
        raw_metrics=intel_data.get("raw_metrics", {}),
        raw_news=intel_data.get("raw_news", []),
        raw_filings=intel_data.get("raw_filings", []),
    )
    db.add(raw_row)

    row = CoreEquityReport(
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


async def get_latest_core_equity_report(db: AsyncSession, ticker: str) -> CoreEquityReport | None:
    """Fetch the latest Core Equity Intel record for a ticker."""
    query = (
        select(CoreEquityReport)
        .where(CoreEquityReport.ticker == ticker.upper())
        .order_by(desc(CoreEquityReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_core_equity_report_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None
) -> CoreEquityReport | None:
    """Fetch Core Equity Intel record for a ticker, optionally on a specific date or as of that date."""
    if date_str:
        query_exact = (
            select(CoreEquityReport)
            .where(CoreEquityReport.ticker == ticker.upper(), func.date(CoreEquityReport.date) == date_str)
            .order_by(desc(CoreEquityReport.date))
            .limit(1)
        )
        exact = (await db.execute(query_exact)).scalar_one_or_none()
        if exact:
            return exact

        query_asof = (
            select(CoreEquityReport)
            .where(CoreEquityReport.ticker == ticker.upper(), func.date(CoreEquityReport.date) <= date_str)
            .order_by(desc(CoreEquityReport.date))
            .limit(1)
        )
        return (await db.execute(query_asof)).scalar_one_or_none()

    return await get_latest_core_equity_report(db, ticker)


async def get_core_equity_report_by_id(db: AsyncSession, intel_id: int) -> CoreEquityReport | None:
    """Fetch a Core Equity Intel record by ID."""
    query = select(CoreEquityReport).where(CoreEquityReport.id == intel_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()




# ==========================================
# Retail Momentum Reports CRUD
# ==========================================

async def save_retail_sentiment_report(
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
) -> RetailSentimentReport:
    """Save the generated Retail Sentiment Report linked to Core Equity Intel."""
    db_report = RetailSentimentReport(
        ticker=ticker.upper(),
        core_intel_id=core_intel_id,
        rank=rank,
        mention_count=mention_count,
        engagement_score=engagement_score,
        community_sentiment=report.community_sentiment,
        community_hype=report.community_hype,
        smart_money_verdict=report.smart_money_verdict,
        raw_insider_data=insider_data or {},
        reconciliation_actionable_insight=report.reconciliation_actionable_insight,
        recommendation=report.recommendation,
        recommendation_rationale=report.recommendation_rationale,
    )
    db.add(db_report)
    await db.commit()
    await db.refresh(db_report)
    return db_report




async def get_distinct_report_dates(db: AsyncSession) -> list[str]:
    """
    Returns a sorted list of unique report dates formatted as YYYY-MM-DD in descending order
    aggregated across Retail, Smart Money, Options Whale, and Synthesis datasets.
    """
    d1 = select(func.date(RetailSentimentReport.date)).distinct()
    d2 = select(func.date(SmartMoneyReport.date)).distinct()
    d3 = select(func.date(SynthesisReport.date)).distinct()
    d4 = select(func.date(OptionsWhaleReport.date)).distinct()

    res1 = (await db.execute(d1)).scalars().all()
    res2 = (await db.execute(d2)).scalars().all()
    res3 = (await db.execute(d3)).scalars().all()
    res4 = (await db.execute(d4)).scalars().all()

    all_dates = set(
        [str(d) for d in res1 if d]
        + [str(d) for d in res2 if d]
        + [str(d) for d in res3 if d]
        + [str(d) for d in res4 if d]
    )
    return sorted(list(all_dates), reverse=True)


async def get_retail_reports_by_date(db: AsyncSession, date_str: str) -> list[RetailSentimentReport]:
    """
    Fetch all Retail reports generated on a specific date (YYYY-MM-DD).
    """
    query = (
        select(RetailSentimentReport)
        .where(func.date(RetailSentimentReport.date) == date_str)
        .order_by(RetailSentimentReport.rank.asc(), RetailSentimentReport.ticker.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_distinct_tracked_tickers(db: AsyncSession) -> list[str]:
    """
    Fetch all distinct ticker symbols that have reports in the database across all engines and synthesis.
    """
    q_retail = select(distinct(RetailSentimentReport.ticker))
    q_smart = select(distinct(SmartMoneyReport.ticker))
    q_options = select(distinct(OptionsWhaleReport.ticker))
    q_synthesis = select(distinct(SynthesisReport.ticker))
    q_core = select(distinct(CoreEquityReport.ticker))

    res_retail = (await db.execute(q_retail)).scalars().all()
    res_smart = (await db.execute(q_smart)).scalars().all()
    res_options = (await db.execute(q_options)).scalars().all()
    res_synthesis = (await db.execute(q_synthesis)).scalars().all()
    res_core = (await db.execute(q_core)).scalars().all()

    all_tickers = set(
        [r for r in res_retail if r]
        + [r for r in res_smart if r]
        + [r for r in res_options if r]
        + [r for r in res_synthesis if r]
        + [r for r in res_core if r]
    )
    return sorted(list(all_tickers))


async def get_ticker_history(db: AsyncSession, ticker: str):
    """
    Fetch all historical reports for a given ticker ordered by date ascending across all engines.
    Unifies Retail Momentum, Smart Money Scout, Options Whale Radar, Synthesis, and Core Equity Intel records.
    """
    sym = ticker.upper()

    query_core = (
        select(CoreEquityReport)
        .where(CoreEquityReport.ticker == sym)
        .order_by(CoreEquityReport.date.asc(), CoreEquityReport.id.asc())
    )
    core_records = list((await db.execute(query_core)).scalars().all())

    query_retail = (
        select(RetailSentimentReport)
        .where(RetailSentimentReport.ticker == sym)
        .order_by(RetailSentimentReport.date.asc(), RetailSentimentReport.id.asc())
    )
    retail_records = list((await db.execute(query_retail)).scalars().all())

    query_smart = (
        select(SmartMoneyReport)
        .where(SmartMoneyReport.ticker == sym)
        .order_by(SmartMoneyReport.date.asc(), SmartMoneyReport.id.asc())
    )
    smart_records = list((await db.execute(query_smart)).scalars().all())

    query_synthesis = (
        select(SynthesisReport)
        .where(SynthesisReport.ticker == sym)
        .order_by(SynthesisReport.date.asc(), SynthesisReport.id.asc())
    )
    synthesis_records = list((await db.execute(query_synthesis)).scalars().all())

    query_options = (
        select(OptionsWhaleReport)
        .where(OptionsWhaleReport.ticker == sym)
        .order_by(OptionsWhaleReport.date.asc(), OptionsWhaleReport.id.asc())
    )
    options_records = list((await db.execute(query_options)).scalars().all())

    if not any([core_records, retail_records, smart_records, synthesis_records, options_records]):
        return []

    # Map buckets by key:
    # Anchor by CoreEquityReport when available; match related engine records by core_intel_id or calendar date.
    buckets_by_core_id: dict[int, dict] = {}
    buckets_by_date: dict[str, dict] = {}
    all_buckets: list[dict] = []

    for c in core_records:
        b = {
            "core": c,
            "retail": None,
            "smart": None,
            "synthesis": None,
            "options": None,
            "date": c.date,
            "core_id": c.id,
        }
        buckets_by_core_id[c.id] = b
        d_str = c.date.strftime("%Y-%m-%d") if c.date else None
        if d_str:
            buckets_by_date[d_str] = b
        all_buckets.append(b)

    def attach_or_create(item, comp_name: str):
        c_id = getattr(item, "core_intel_id", None)
        d_str = item.date.strftime("%Y-%m-%d") if getattr(item, "date", None) else None

        # 1. Match by explicit core_intel_id
        if c_id and c_id in buckets_by_core_id:
            buckets_by_core_id[c_id][comp_name] = item
            return

        # 2. Match by calendar date with existing core bucket
        if d_str and d_str in buckets_by_date:
            buckets_by_date[d_str][comp_name] = item
            return

        # 3. Create a new standalone bucket
        b = {
            "core": None,
            "retail": None,
            "smart": None,
            "synthesis": None,
            "options": None,
            "date": item.date,
            "core_id": None,
        }
        b[comp_name] = item
        if d_str:
            buckets_by_date[d_str] = b
        all_buckets.append(b)

    for r in retail_records:
        attach_or_create(r, "retail")

    for s in smart_records:
        attach_or_create(s, "smart")

    for syn in synthesis_records:
        attach_or_create(syn, "synthesis")

    for opt in options_records:
        attach_or_create(opt, "options")

    history_points = []
    for b in all_buckets:
        core = b["core"]
        retail = b["retail"]
        smart = b["smart"]
        synthesis = b["synthesis"]
        options = b["options"]

        curr_p = (
            (core and core.current_price)
            or (retail and retail.current_price)
            or (smart and smart.current_price)
        )
        targ_p = (
            (core and core.target_price)
            or (retail and retail.target_price)
            or (smart and smart.target_price)
        )
        raw_m = (
            (core and core.raw_metrics)
            or (retail and retail.raw_metrics)
            or (smart and smart.raw_metrics)
            or {}
        )

        rec = None
        if retail and retail.recommendation:
            rec = retail.recommendation
        elif synthesis and synthesis.recommended_action:
            action = synthesis.recommended_action.upper()
            if any(w in action for w in ["BUY", "ROCKET", "ACCUMULATION"]):
                rec = "BUY"
            elif any(w in action for w in ["SELL", "AVOID", "SHORT", "TRAP"]):
                rec = "SELL"
            else:
                rec = "HOLD"
        elif smart:
            is_alpha = "Alpha" in (smart.conviction_tier or "") or "High" in (smart.conviction_tier or "")
            rec = "BUY" if is_alpha else "HOLD"
        else:
            rec = "HOLD"

        rec_rationale = (
            (retail and retail.recommendation_rationale)
            or (synthesis and synthesis.synthesis_diagnosis)
            or (smart and smart.actionable_thesis)
            or "Core equity research baseline."
        )

        smart_verdict = (
            (retail and retail.smart_money_verdict)
            or (synthesis and synthesis.smart_money_flow)
            or (smart and smart.conviction_tier)
            or "Neutral"
        )

        comm_sentiment = (
            (retail and retail.community_sentiment)
            or (synthesis and synthesis.retail_sentiment)
            or "Stealth (Unmonitored by Retail)"
        )

        comm_hype = (
            (retail and retail.community_hype)
            or (synthesis and f"Retail Phase: {synthesis.retail_awareness_level}")
            or (smart and smart.top_buyer_summary)
            or "No active Reddit discussion tracked."
        )

        gt_status = (
            (core and core.ground_truth_status)
            or (retail and retail.ground_truth_status)
            or (smart and smart.ground_truth_status)
            or "Objective financial and SEC filing evaluation."
        )

        risk_score = (
            (core and core.risk_score)
            or (retail and retail.reconciliation_risk_score)
            or (smart and smart.risk_score)
            or "Medium"
        )

        actionable_insight = (
            (retail and retail.reconciliation_actionable_insight)
            or (smart and smart.actionable_thesis)
            or (synthesis and synthesis.synthesis_diagnosis)
            or (core and core.actionable_insight)
            or "Track quarterly filings and market signals."
        )

        point_id = (
            (retail and retail.id)
            or (smart and smart.id)
            or (options and options.id)
            or (core and core.id)
            or (synthesis and synthesis.id)
            or 0
        )

        run_date = (
            (core and core.date)
            or (retail and retail.date)
            or (smart and smart.date)
            or (synthesis and synthesis.date)
            or (options and options.date)
            or b.get("date")
        )

        point = SimpleNamespace(
            id=point_id,
            ticker=sym,
            date=run_date,
            current_price=curr_p,
            target_price=targ_p,
            community_sentiment=comm_sentiment,
            community_hype=comm_hype,
            ground_truth_status=gt_status,
            reconciliation_risk_score=risk_score,
            reconciliation_actionable_insight=actionable_insight,
            recommendation=rec,
            recommendation_rationale=rec_rationale,
            smart_money_verdict=smart_verdict,
            raw_metrics=raw_m,
        )
        history_points.append(point)

    history_points.sort(key=lambda x: x.date if x.date else datetime.min.replace(tzinfo=timezone.utc))
    return history_points


async def get_latest_retail_report(db: AsyncSession, ticker: str) -> RetailSentimentReport | None:
    """Fetch the latest Retail report for a specific ticker."""
    query = (
        select(RetailSentimentReport)
        .where(RetailSentimentReport.ticker == ticker.upper())
        .order_by(desc(RetailSentimentReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_retail_report_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None
) -> RetailSentimentReport | None:
    """Fetch Retail report for a ticker, optionally on a specific date."""
    if date_str:
        query = (
            select(RetailSentimentReport)
            .where(RetailSentimentReport.ticker == ticker.upper(), func.date(RetailSentimentReport.date) == date_str)
            .order_by(desc(RetailSentimentReport.date))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    return await get_latest_retail_report(db, ticker)


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


async def save_insider_trades_raw(db: AsyncSession, trades: list[dict]):
    """Persist raw Form 4 insider transactions."""
    for t in trades:
        row = InsiderTradesRaw(
            ticker=str(t.get("ticker", "")).upper(),
            filing_date=str(t.get("filing_date") or ""),
            trade_date=str(t.get("trade_date") or ""),
            insider_name=str(t.get("insider_name") or "Unknown"),
            position=str(t.get("title") or t.get("position") or ""),
            transaction_type=str(t.get("trade_type") or "Purchase"),
            shares=float(t.get("qty") or t.get("shares") or 0.0),
            price=str(t.get("price") or ""),
            total_value=float(t.get("value") or t.get("total_value") or 0.0),
            ownership=str(t.get("delta_own") or t.get("ownership") or ""),
            filing_details=t.get("company_name"),
        )
        db.add(row)
    await db.commit()


async def save_congress_trades_raw(db: AsyncSession, trades: list[dict]):
    """Persist raw Congressional STOCK Act disclosures."""
    for t in trades:
        row = CongressTradesRaw(
            ticker=str(t.get("ticker", "")).upper(),
            trade_date=str(t.get("trade_date") or ""),
            politician_name=str(t.get("politician") or t.get("politician_name") or "Congressional Member"),
            chamber=t.get("chamber"),
            party=t.get("party"),
            committee=t.get("committee"),
            transaction_type=str(t.get("transaction_type") or "BUY"),
            amount_range=str(t.get("amount_range") or ""),
            source_url=str(t.get("source_title") or t.get("source_url") or ""),
            snippet=str(t.get("snippet") or ""),
        )
        db.add(row)
    await db.commit()

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
    """Save an Engine 2 catalyst intelligence report linked to CoreEquityReport."""
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


async def get_smart_money_report_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None
) -> SmartMoneyReport | None:
    """Fetch Smart Money report for a ticker, optionally on a specific date."""
    if date_str:
        query = (
            select(SmartMoneyReport)
            .where(SmartMoneyReport.ticker == ticker.upper(), func.date(SmartMoneyReport.date) == date_str)
            .order_by(desc(SmartMoneyReport.date))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    return await get_latest_smart_money_report(db, ticker)


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

async def save_synthesis_reports(db: AsyncSession, records: list[dict]) -> list[SynthesisReport]:
    """Save cross-engine synthesis archetype classifications."""
    saved = []
    for item in records:
        row = SynthesisReport(
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
            recommended_action=item.get("recommended_action", "PASS"),
            whale_options_flow=item.get("whale_options_flow"),
            whale_options_score=item.get("whale_options_score", 0.0),
            put_call_ratio=item.get("put_call_ratio"),
        )
        db.add(row)
        saved.append(row)
    await db.commit()
    return saved


async def get_latest_synthesis_reports(db: AsyncSession) -> list[SynthesisReport]:
    """Retrieve the latest synthesis matrix records, deduplicated by ticker."""
    latest_ts_query = select(func.max(SynthesisReport.date))
    latest_ts_res = await db.execute(latest_ts_query)
    latest_ts = latest_ts_res.scalar_one_or_none()
    if not latest_ts:
        return []

    # Fetch recent records within 15 seconds of the latest timestamp
    query = (
        select(SynthesisReport)
        .where(SynthesisReport.date >= latest_ts - timedelta(seconds=15))
        .order_by(SynthesisReport.date.desc(), SynthesisReport.timing_edge_score.desc())
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


async def get_synthesis_reports_by_date(db: AsyncSession, date_str: str) -> list[SynthesisReport]:
    """Retrieve synthesis matrix records for a specific date (YYYY-MM-DD), deduplicated by ticker."""
    query = (
        select(SynthesisReport)
        .where(func.date(SynthesisReport.date) == date_str)
        .order_by(SynthesisReport.date.desc(), SynthesisReport.timing_edge_score.desc())
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


async def get_synthesis_report_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None
) -> SynthesisReport | None:
    """Retrieve the synthesis record for a ticker, optionally on a specific date."""
    if date_str:
        query = (
            select(SynthesisReport)
            .where(SynthesisReport.ticker == ticker.upper(), func.date(SynthesisReport.date) == date_str)
            .order_by(desc(SynthesisReport.date))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    query = (
        select(SynthesisReport)
        .where(SynthesisReport.ticker == ticker.upper())
        .order_by(desc(SynthesisReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()



async def get_ticker_archetype_history(db: AsyncSession, ticker: str) -> list[SynthesisReport]:
    """Retrieve chronological synthesis archetype progression for a single ticker."""
    query = (
        select(SynthesisReport)
        .where(SynthesisReport.ticker == ticker.upper())
        .order_by(SynthesisReport.date.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


# ==========================================
# Engine 3: Institutional Whale Options CRUD
# ==========================================

async def save_options_whale_tickers(db: AsyncSession, candidates: list[dict]) -> list[OptionsWhaleTicker]:
    """Save the top-ranked options whale candidates from Engine 3."""
    saved = []
    for idx, item in enumerate(candidates):
        row = OptionsWhaleTicker(
            ticker=item["ticker"].upper(),
            rank=idx + 1,
            whale_score=item.get("whale_score", 0.0),
            unusual_oi_multiplier=item.get("unusual_oi_multiplier", 1.0),
            net_bullish_premium=item.get("net_bullish_premium", 0.0),
            put_call_ratio=item.get("put_call_ratio", 1.0),
            top_strike_summary=item.get("top_strike_summary", "")
        )
        db.add(row)
        saved.append(row)
    await db.commit()
    return saved


async def get_latest_options_whale_tickers(db: AsyncSession) -> list[OptionsWhaleTicker]:
    """Retrieve the most recent run's options whale tickers."""
    latest_ts_query = select(func.max(OptionsWhaleTicker.date))
    latest_ts_res = await db.execute(latest_ts_query)
    latest_ts = latest_ts_res.scalar_one_or_none()
    if not latest_ts:
        return []

    query = (
        select(OptionsWhaleTicker)
        .where(OptionsWhaleTicker.date >= latest_ts - timedelta(seconds=15))
        .order_by(OptionsWhaleTicker.rank.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def save_options_whale_report(
    db: AsyncSession,
    ticker: str,
    whale_data: dict,
    core_intel_id: int | None = None,
    rank: int | None = None,
) -> OptionsWhaleReport:
    """Save an individual Engine 3 Options Whale report linked to Core Equity Intel."""
    sym = ticker.upper()
    core_intel = None
    if core_intel_id:
        core_intel = await get_core_equity_report_by_id(db, core_intel_id)
    if not core_intel:
        core_intel = await get_latest_core_equity_report(db, sym)

    c_name = core_intel.company_name if core_intel else sym
    sec = core_intel.sector if core_intel else None
    ind = core_intel.industry if core_intel else None
    curr_p = whale_data.get("current_price") or (core_intel.current_price if core_intel else None)
    targ_p = core_intel.target_price if core_intel else None

    report = OptionsWhaleReport(
        ticker=sym,
        core_intel_id=core_intel.id if core_intel else core_intel_id,
        company_name=c_name,
        sector=sec,
        industry=ind,
        current_price=curr_p,
        target_price=targ_p,
        rank=rank,
        whale_score=whale_data.get("whale_score", 0.0),
        unusual_oi_multiplier=whale_data.get("unusual_oi_multiplier", 1.0),
        put_call_ratio=whale_data.get("put_call_ratio", 1.0),
        net_bullish_premium=whale_data.get("net_bullish_premium", 0.0),
        sentiment_bias=whale_data.get("sentiment_bias", "Neutral Tape"),
        top_strike_summary=whale_data.get("top_strike_summary", ""),
        unusual_contracts=whale_data.get("unusual_contracts", []),
        ground_truth_status=core_intel.ground_truth_status if core_intel else "Objective financial evaluation.",
        ground_truth_filings_news=core_intel.ground_truth_filings_news if core_intel else None,
        events_happenings=core_intel.events_happenings if core_intel else None,
        risk_score=core_intel.risk_score if core_intel else "Medium",
        raw_metrics=core_intel.raw_metrics if core_intel else {},
    )
    for c in whale_data.get("unusual_contracts", []):
        opt_raw = OptionsWhaleRaw(
            ticker=sym,
            timestamp=str(c.get("timestamp") or datetime.now(timezone.utc).isoformat()),
            strike=float(c.get("strike", 0.0)) if c.get("strike") is not None else None,
            expiry_date=str(c.get("expiry") or c.get("expiry_date") or ""),
            option_type=str(c.get("type") or c.get("option_type") or "CALL"),
            volume=int(c.get("volume", 0)),
            open_interest=int(c.get("open_interest", 0)),
            volume_oi_ratio=float(c.get("ratio") or c.get("volume_oi_ratio", 0.0)),
            spot_price=float(c.get("spot") or curr_p or 0.0),
            premium_spent=float(c.get("premium") or c.get("premium_spent", 0.0)),
            sentiment=str(c.get("sentiment") or whale_data.get("sentiment_bias") or ""),
        )
        db.add(opt_raw)

    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_latest_options_whale_report(db: AsyncSession, ticker: str) -> OptionsWhaleReport | None:
    """Fetch the latest Options Whale report for a ticker."""
    query = (
        select(OptionsWhaleReport)
        .where(OptionsWhaleReport.ticker == ticker.upper())
        .order_by(desc(OptionsWhaleReport.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_options_whale_report_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None
) -> OptionsWhaleReport | None:
    """Fetch Options Whale report for a ticker, optionally on a specific date."""
    if date_str:
        query = (
            select(OptionsWhaleReport)
            .where(OptionsWhaleReport.ticker == ticker.upper(), func.date(OptionsWhaleReport.date) == date_str)
            .order_by(desc(OptionsWhaleReport.date))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    return await get_latest_options_whale_report(db, ticker)


async def get_options_reports_by_date(db: AsyncSession, date_str: str) -> list[OptionsWhaleReport]:
    """Retrieve all Options Whale reports for a specific date (YYYY-MM-DD)."""
    query = (
        select(OptionsWhaleReport)
        .where(func.date(OptionsWhaleReport.date) == date_str)
        .order_by(OptionsWhaleReport.rank.asc(), desc(OptionsWhaleReport.whale_score))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


# ==========================================
# Model Calibration & Backtest CRUD
# ==========================================

async def save_model_calibration_run(
    db: AsyncSession,
    sample_runs_count: int,
    overall_hit_rate_t30: float,
    avg_alpha_vs_spy_t30: float,
    max_drawdown: float,
    archetype_scorecard: dict,
    active_weights: dict,
    recommended_weights: dict,
    is_applied: int = 0
) -> ModelCalibrationRun:
    """Save a model calibration scorecard evaluation and weights run."""
    run = ModelCalibrationRun(
        sample_runs_count=sample_runs_count,
        overall_hit_rate_t30=overall_hit_rate_t30,
        avg_alpha_vs_spy_t30=avg_alpha_vs_spy_t30,
        max_drawdown=max_drawdown,
        archetype_scorecard=archetype_scorecard,
        active_weights=active_weights,
        recommended_weights=recommended_weights,
        is_applied=is_applied
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def get_latest_model_calibration_run(db: AsyncSession) -> ModelCalibrationRun | None:
    """Retrieve the most recent calibration scorecard evaluation."""
    query = (
        select(ModelCalibrationRun)
        .order_by(desc(ModelCalibrationRun.date))
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()
