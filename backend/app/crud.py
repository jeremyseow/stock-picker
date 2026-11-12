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
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)
from app.llm_schemas import RetailOverlayAnalysis, TrajectoryAnalysis
from app.reddit_scraper import get_target_subreddits


async def save_retail_social_raw(db: AsyncSession, raw_social_items: list[dict]):
    """Save raw social signals and Reddit discussions to retail_social_raw."""
    default_subreddits = ", ".join(get_target_subreddits())
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for idx, item in enumerate(raw_social_items, start=1):
        sym = item["ticker"].upper()
        raw_social = RetailSocialRaw(
            ticker=sym,
            platform=item.get("platform", "reddit"),
            post_id=item.get("post_id") or f"rank_{idx}_{today_str}",
            subreddit=item.get("subreddit") or default_subreddits,
            title=item.get("title") or item.get("post_title") or f"Reddit discussions for {sym}",
            author=item.get("author") or "reddit_community",
            score=int(item.get("score") or item.get("engagement_score") or 0),
            comment_count=int(item.get("comment_count") or item.get("mention_count") or 0),
            post_url=item.get("post_url") or f"https://www.reddit.com/search/?q={sym}",
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
    """Save foundational equity intelligence (CoreEquityRaw for raw blobs + CoreEquityReport for LLM synthesis)."""
    raw_row = CoreEquityRaw(
        ticker=intel_data["ticker"].upper(),
        company_name=intel_data.get("company_name"),
        sector=intel_data.get("sector"),
        industry=intel_data.get("industry"),
        current_price=intel_data.get("current_price"),
        target_price=intel_data.get("target_price"),
        raw_metrics=intel_data.get("raw_metrics", {}),
        raw_news=intel_data.get("raw_news", []),
        raw_filings=intel_data.get("raw_filings", []),
    )
    db.add(raw_row)
    await db.flush()

    row = CoreEquityReport(
        ticker=intel_data["ticker"].upper(),
        core_raw_id=raw_row.id,
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
    report: RetailOverlayAnalysis,
    core_intel_id: int | None = None,
    daily_ticker_id: int | None = None,
    rank: int | None = None,
    mention_count: int = 0,
    engagement_score: float = 0.0,
) -> RetailSentimentReport:
    """Save Engine 1's pure Retail Sentiment Report linked to CoreEquityReport and DailyTicker."""
    sym = ticker.upper()
    if daily_ticker_id is None and (rank is not None or mention_count or engagement_score):
        dt_row = DailyTicker(
            ticker=sym,
            rank=rank,
            mention_count=mention_count,
            engagement_score=engagement_score,
        )
        db.add(dt_row)
        await db.flush()
        daily_ticker_id = dt_row.id

    db_report = RetailSentimentReport(
        ticker=sym,
        core_intel_id=core_intel_id,
        daily_ticker_id=daily_ticker_id,
        community_sentiment=report.community_sentiment,
        community_hype=report.community_hype,
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
    Fetch all Retail reports generated on a specific date (YYYY-MM-DD),
    ordered by linked DailyTicker.rank ascending then ticker ascending.
    """
    query = (
        select(RetailSentimentReport)
        .where(func.date(RetailSentimentReport.date) == date_str)
    )
    result = await db.execute(query)
    reports = list(result.scalars().all())
    reports.sort(key=lambda r: (r.rank if r.rank is not None else 999999, r.ticker or ""))
    return reports


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
            (smart and smart.conviction_tier)
            or (synthesis and synthesis.smart_money_flow)
            or await get_smart_money_verdict_for_ticker(
                db, sym, date_str=b["date"].strftime("%Y-%m-%d") if b.get("date") else None
            )
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
    """Persist raw Form 4 insider transactions (BUY, SELL, OTHER) with deduplication."""
    for t in trades:
        sym = str(t.get("ticker", "")).upper()
        if not sym:
            continue
        raw_type = str(t.get("trade_type") or t.get("transaction_type") or "BUY").strip().upper()
        if raw_type in ("PURCHASE", "P", "P - PURCHASE", "BUY"):
            norm_type = "BUY"
        elif "SALE" in raw_type or raw_type in ("S", "SELL"):
            norm_type = "SELL"
        else:
            norm_type = "OTHER"

        insider_name = str(t.get("insider_name") or "Unknown")
        trade_date = str(t.get("trade_date") or "")
        shares_val = float(t.get("qty") or t.get("shares") or 0.0)

        existing = (
            await db.execute(
                select(InsiderTradesRaw.id).where(
                    InsiderTradesRaw.ticker == sym,
                    InsiderTradesRaw.insider_name == insider_name,
                    InsiderTradesRaw.trade_date == trade_date,
                    InsiderTradesRaw.transaction_type == norm_type,
                    InsiderTradesRaw.shares == shares_val,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue

        row = InsiderTradesRaw(
            ticker=sym,
            filing_date=str(t.get("filing_date") or ""),
            trade_date=trade_date,
            insider_name=insider_name,
            position=str(t.get("title") or t.get("position") or ""),
            transaction_type=norm_type,
            shares=shares_val,
            price=str(t.get("price") or ""),
            total_value=float(t.get("value") or t.get("total_value") or 0.0),
            ownership=str(t.get("delta_own") or t.get("ownership") or ""),
            filing_details=t.get("company_name") or t.get("filing_details"),
        )
        db.add(row)
    await db.commit()


async def get_insider_trades_by_ticker(
    db: AsyncSession,
    ticker: str,
    date_str: str | None = None,
    tx_type: str | None = None,
    limit: int = 25,
) -> list[InsiderTradesRaw]:
    """Fetch Engine 2 raw Form 4 transactions for a ticker."""
    query = select(InsiderTradesRaw).where(InsiderTradesRaw.ticker == ticker.upper())
    if date_str:
        query = query.where(func.date(InsiderTradesRaw.captured_at) <= date_str)
    if tx_type:
        query = query.where(InsiderTradesRaw.transaction_type == tx_type.upper())
    query = query.order_by(desc(InsiderTradesRaw.trade_date), desc(InsiderTradesRaw.id)).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


async def get_smart_money_verdict_for_ticker(
    db: AsyncSession,
    ticker: str,
    date_str: str | None = None,
    smart_money_rep: SmartMoneyReport | None = None,
    synthesis_rec: SynthesisReport | None = None,
) -> str:
    """Derive a concise Smart Money / Form 4 insider verdict strictly from Engine 2 & Synthesis data."""
    sym = ticker.upper()
    if smart_money_rep is None:
        smart_money_rep = await get_smart_money_report_by_ticker(db, sym, date_str)
    if smart_money_rep and smart_money_rep.conviction_tier:
        return smart_money_rep.conviction_tier

    if synthesis_rec and synthesis_rec.smart_money_flow and synthesis_rec.smart_money_flow != "Neutral":
        return synthesis_rec.smart_money_flow

    rows = await get_insider_trades_by_ticker(db, sym, date_str=date_str, limit=25)
    if not rows:
        return "Neutral"

    buy_val = sum((r.total_value or 0.0) for r in rows if r.transaction_type == "BUY")
    sell_val = sum((r.total_value or 0.0) for r in rows if r.transaction_type == "SELL")
    buy_sh = sum((r.shares or 0.0) for r in rows if r.transaction_type == "BUY")
    sell_sh = sum((r.shares or 0.0) for r in rows if r.transaction_type == "SELL")

    if sell_val > buy_val or (sell_sh > buy_sh and sell_sh > 0):
        return "Bearish Divergence: C-Suite Selling"
    if buy_val > sell_val or buy_sh > 0:
        return "Bullish Accumulation"
    return "Neutral Insider Flow"


async def build_engine2_insider_payload(
    db: AsyncSession,
    ticker: str,
    date_str: str | None = None,
    smart_money_rep: SmartMoneyReport | None = None,
    synthesis_rec: SynthesisReport | None = None,
) -> dict:
    """
    Assemble Form 4 outflow ledger, congressional trades, and raw insider summary strictly
    from Engine 2 raw tables (insider_trades_raw & congress_trades_raw) and SmartMoneyReport.
    """
    sym = ticker.upper()
    insider_rows = await get_insider_trades_by_ticker(db, sym, date_str=date_str, limit=25)
    congress_rows = await get_congress_trades_by_ticker(db, sym, date_str=date_str, limit=15)

    outflow_ledger = []
    total_sell_volume = 0.0
    sellers = []
    purchases_shares = 0.0
    purchases_trans = 0
    sales_shares = 0.0
    sales_trans = 0
    recent_transactions = []

    for r in insider_rows:
        sh = float(r.shares or 0.0)
        val = float(r.total_value or 0.0)
        tx_t = (r.transaction_type or "OTHER").upper()
        if tx_t == "BUY":
            purchases_shares += sh
            purchases_trans += 1
        elif tx_t == "SELL":
            sales_shares += sh
            sales_trans += 1
            total_sell_volume += val

            val_str = f"${val:,.0f}" if val else "-"
            if val >= 1e6:
                val_str = f"${val/1e6:.1f}M"
            elif val >= 1e3:
                val_str = f"${val/1e3:.0f}k"

            name = r.insider_name or "Executive"
            pos = r.position or "Officer"
            seller_desc = f"{name} ({pos})"
            if seller_desc not in sellers:
                sellers.append(seller_desc)

            outflow_ledger.append({
                "date": r.trade_date or r.filing_date,
                "seller": name,
                "role": pos,
                "shares": int(sh) if sh else None,
                "price": r.price or "-",
                "value": val_str,
                "details": r.filing_details or "Open Market Sale",
            })

        recent_transactions.append({
            "date": r.trade_date or r.filing_date,
            "insider": r.insider_name,
            "position": r.position,
            "shares": int(sh),
            "value": int(val),
            "price": r.price or "-",
            "type": tx_t,
            "details": r.filing_details or tx_t,
            "ownership": r.ownership or "",
        })

    top_seller_summary = None
    if sellers:
        top_seller_summary = ", ".join(sellers[:2])
        if len(sellers) > 2:
            top_seller_summary += f" +{len(sellers)-2} others"

    congressional_trades = [
        {
            "title": f"{c.politician_name} ({c.chamber or 'Congress'}{' - ' + c.party if c.party else ''}) {c.transaction_type} {c.amount_range}",
            "link": c.source_url if (c.source_url and c.source_url.startswith("http")) else None,
            "snippet": c.snippet or f"Trade Date: {c.trade_date} | Disclosed: {c.filing_date or 'N/A'}",
        }
        for c in congress_rows
    ]

    verdict = await get_smart_money_verdict_for_ticker(
        db, sym, date_str=date_str, smart_money_rep=smart_money_rep, synthesis_rec=synthesis_rec
    )
    net_shares = purchases_shares - sales_shares

    summary_text = smart_money_rep.actionable_thesis if smart_money_rep else None
    if not summary_text and insider_rows:
        if sales_trans > purchases_trans:
            summary_text = f"{sales_trans} Form 4 sale(s) totaling {int(sales_shares):,} shares by {top_seller_summary or 'insiders'}."
        elif purchases_trans > 0:
            summary_text = f"{purchases_trans} Form 4 purchase(s) totaling {int(purchases_shares):,} shares."

    raw_insider_data = {
        "has_data": bool(insider_rows or congress_rows or smart_money_rep),
        "purchases_shares": purchases_shares,
        "purchases_trans": purchases_trans,
        "sales_shares": sales_shares,
        "sales_trans": sales_trans,
        "net_shares": net_shares,
        "sentiment_label": verdict,
        "recent_transactions": recent_transactions,
        "congressional_trades": congressional_trades,
        "insider_activity_summary": summary_text,
    }

    return {
        "outflow_ledger": outflow_ledger,
        "total_sell_volume": total_sell_volume,
        "top_seller_summary": top_seller_summary,
        "smart_money_verdict": verdict,
        "raw_insider_data": raw_insider_data,
    }


async def save_congress_trades_raw(db: AsyncSession, trades: list[dict]):
    """Persist raw Congressional STOCK Act disclosures."""
    for t in trades:
        row = CongressTradesRaw(
            ticker=str(t.get("ticker", "")).upper(),
            filing_date=str(t.get("filing_date") or ""),
            trade_date=str(t.get("trade_date") or ""),
            politician_name=str(t.get("politician") or t.get("politician_name") or "Congressional Member"),
            chamber=t.get("chamber"),
            party=t.get("party"),
            committee=t.get("committee"),
            transaction_type=str(t.get("transaction_type") or "BUY"),
            amount_range=str(t.get("amount_range") or ""),
            source_url=str(t.get("source_url") or t.get("source_title") or ""),
            snippet=str(t.get("snippet") or ""),
        )
        db.add(row)
    await db.commit()


async def get_congress_trades_by_ticker(
    db: AsyncSession, ticker: str, date_str: str | None = None, limit: int = 10
) -> list[CongressTradesRaw]:
    """Fetch Engine 2 Congressional STOCK Act disclosures for a given ticker."""
    query = select(CongressTradesRaw).where(CongressTradesRaw.ticker == ticker.upper())
    if date_str:
        query = query.where(func.date(CongressTradesRaw.captured_at) == date_str)
    query = query.order_by(desc(CongressTradesRaw.captured_at), desc(CongressTradesRaw.id)).limit(limit)
    res = await db.execute(query)
    return list(res.scalars().all())


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
    core_intel_id: int | None = None,
    smart_money_ticker_id: int | None = None,
) -> SmartMoneyReport:
    """Save an Engine 2 catalyst intelligence report linked to CoreEquityReport and SmartMoneyTicker."""
    sym = report_data["ticker"].upper()
    if smart_money_ticker_id is None:
        existing_tk = (
            await db.execute(
                select(SmartMoneyTicker)
                .where(SmartMoneyTicker.ticker == sym)
                .order_by(desc(SmartMoneyTicker.date))
                .limit(1)
            )
        ).scalar_one_or_none()
        if existing_tk and any(
            k in report_data for k in ("rank", "conviction_score", "cluster_count", "total_buy_volume", "top_buyer_summary")
        ):
            # Create a matching leaderboard row if caller did not pass smart_money_ticker_id explicitly
            tk_row = SmartMoneyTicker(
                ticker=sym,
                rank=report_data.get("rank"),
                conviction_score=report_data.get("conviction_score", 0.0),
                insider_score=report_data.get("insider_score", 0.0),
                political_score=report_data.get("political_score", 0.0),
                cluster_count=report_data.get("cluster_count", 0),
                total_buy_volume=report_data.get("total_buy_volume", 0.0),
                top_buyer_summary=report_data.get("top_buyer_summary", ""),
            )
            db.add(tk_row)
            await db.flush()
            smart_money_ticker_id = tk_row.id
        elif existing_tk:
            smart_money_ticker_id = existing_tk.id

    row = SmartMoneyReport(
        ticker=sym,
        core_intel_id=core_intel_id,
        smart_money_ticker_id=smart_money_ticker_id,
        conviction_tier=report_data.get("conviction_tier", "High Conviction Catalyst Buy"),
        inflow_ledger=report_data.get("inflow_ledger", []),
        political_catalyst_analysis=report_data.get("political_catalyst_analysis", ""),
        corporate_catalyst_analysis=report_data.get("corporate_catalyst_analysis", ""),
        catalyst_horizon=report_data.get("catalyst_horizon", ""),
        actionable_thesis=report_data.get("actionable_thesis", ""),
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
    """Fetch all Smart Money reports generated on a specific date (YYYY-MM-DD), ordered by rank & conviction."""
    query = (
        select(SmartMoneyReport)
        .where(func.date(SmartMoneyReport.date) == date_str)
    )
    result = await db.execute(query)
    reports = list(result.scalars().all())
    reports.sort(key=lambda r: (r.rank if r.rank is not None else 999999, -(r.conviction_score or 0.0)))
    return reports


# ==========================================
# Cross-Engine Synthesis CRUD
# ==========================================

async def save_synthesis_reports(db: AsyncSession, records: list[dict]) -> list[SynthesisReport]:
    """Save cross-engine synthesis archetype classifications linked via FKs to engine reports."""
    saved = []
    for item in records:
        row = SynthesisReport(
            ticker=item["ticker"].upper(),
            core_intel_id=item.get("core_intel_id"),
            retail_report_id=item.get("retail_report_id"),
            smart_money_report_id=item.get("smart_money_report_id"),
            options_whale_report_id=item.get("options_whale_report_id"),
            archetype=item.get("archetype", "Market Noise"),
            smart_money_flow=item.get("smart_money_flow"),
            whale_options_flow=item.get("whale_options_flow"),
            retail_awareness_level=item.get("retail_awareness_level", "Zero Awareness (Stealth)"),
            timing_edge_score=item.get("timing_edge_score", 0.0),
            synthesis_diagnosis=item.get("synthesis_diagnosis", ""),
            recommended_action=item.get("recommended_action", "PASS"),
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
    options_whale_ticker_id: int | None = None,
    rank: int | None = None,
) -> OptionsWhaleReport:
    """
    Save an Engine 3 Options Whale report linked to CoreEquityReport and OptionsWhaleTicker,
    persisting all unusual contracts exclusively in OptionsWhaleRaw.
    """
    sym = ticker.upper()
    core_intel = None
    if core_intel_id:
        core_intel = await get_core_equity_report_by_id(db, core_intel_id)
    if not core_intel:
        core_intel = await get_latest_core_equity_report(db, sym)

    curr_p = whale_data.get("current_price") or (core_intel.current_price if core_intel else None)

    if options_whale_ticker_id is None:
        tk_row = OptionsWhaleTicker(
            ticker=sym,
            rank=rank,
            whale_score=whale_data.get("whale_score", 0.0),
            unusual_oi_multiplier=whale_data.get("unusual_oi_multiplier", 1.0),
            net_bullish_premium=whale_data.get("net_bullish_premium", 0.0),
            put_call_ratio=whale_data.get("put_call_ratio", 1.0),
            top_strike_summary=whale_data.get("top_strike_summary", ""),
        )
        db.add(tk_row)
        await db.flush()
        options_whale_ticker_id = tk_row.id

    raw_contract_objs: list[OptionsWhaleRaw] = []
    for c in whale_data.get("unusual_contracts", []):
        opt_raw = OptionsWhaleRaw(
            ticker=sym,
            timestamp=str(c.get("timestamp") or datetime.now(timezone.utc).isoformat()),
            strike=float(c.get("strike", 0.0)) if c.get("strike") is not None else None,
            expiry_date=str(c.get("expiration") or c.get("expiry") or c.get("expiry_date") or ""),
            dte=int(c["dte"]) if c.get("dte") is not None else None,
            option_type=str(c.get("type") or c.get("option_type") or "CALL"),
            volume=int(c.get("volume", 0)),
            open_interest=int(c.get("open_interest", 0)),
            volume_oi_ratio=float(c.get("ratio") or c.get("volume_oi_ratio", 0.0)),
            spot_price=float(c.get("spot") or curr_p or 0.0),
            premium_spent=float(c.get("premium") or c.get("premium_spent", 0.0)),
            sentiment=str(c.get("sentiment") or whale_data.get("sentiment_bias") or ""),
            is_otm=bool(c["is_otm"]) if c.get("is_otm") is not None else None,
            is_sweep=bool(c["is_sweep"]) if c.get("is_sweep") is not None else None,
        )
        raw_contract_objs.append(opt_raw)

    if raw_contract_objs:
        db.add_all(raw_contract_objs)
        await db.flush()

    report = OptionsWhaleReport(
        ticker=sym,
        core_intel_id=core_intel.id if core_intel else core_intel_id,
        options_whale_ticker_id=options_whale_ticker_id,
        sentiment_bias=whale_data.get("sentiment_bias", "Neutral Tape"),
        raw_contracts=raw_contract_objs,
    )
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
    """Retrieve all Options Whale reports for a specific date (YYYY-MM-DD), ordered by rank & whale_score."""
    query = (
        select(OptionsWhaleReport)
        .where(func.date(OptionsWhaleReport.date) == date_str)
    )
    result = await db.execute(query)
    reports = list(result.scalars().all())
    reports.sort(key=lambda r: (r.rank if r.rank is not None else 999999, -(r.whale_score or 0.0)))
    return reports


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
    is_applied: int = 0,
    scorecard_data: dict | None = None
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
        is_applied=is_applied,
        scorecard_data=scorecard_data,
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


# ==========================================
# Paper Trading Portfolio CRUD
# ==========================================

async def get_or_create_portfolio_account(
    db: AsyncSession, name: str = "Primary Fund", initial_balance: float = 100000.0
) -> PortfolioAccount:
    """Retrieve existing primary paper trading account or initialize default account with $100k."""
    query = select(PortfolioAccount).where(PortfolioAccount.name == name).limit(1)
    result = await db.execute(query)
    account = result.scalar_one_or_none()
    if account is None:
        account = PortfolioAccount(
            name=name,
            initial_balance=initial_balance,
            cash_balance=initial_balance,
            total_equity=initial_balance,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
    return account


async def get_portfolio_account(
    db: AsyncSession, account_id: int | None = None
) -> PortfolioAccount | None:
    """Retrieve portfolio account by ID or default first account."""
    if account_id:
        query = select(PortfolioAccount).where(PortfolioAccount.id == account_id)
    else:
        query = select(PortfolioAccount).order_by(PortfolioAccount.id.asc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_portfolio_account(
    db: AsyncSession,
    account: PortfolioAccount,
    cash_balance: float | None = None,
    total_equity: float | None = None,
) -> PortfolioAccount:
    """Update portfolio account cash balance and total equity."""
    if cash_balance is not None:
        account.cash_balance = round(cash_balance, 2)
    if total_equity is not None:
        account.total_equity = round(total_equity, 2)
    account.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(account)
    return account


async def create_portfolio_position(
    db: AsyncSession,
    account_id: int,
    ticker: str,
    archetype: str,
    conviction_score: float,
    shares: int,
    entry_price: float,
    stop_loss_price: float,
    target_price: float | None = None,
    entry_date: datetime | None = None,
    spy_entry_price: float | None = None,
) -> PortfolioPosition:
    """Create a new open paper position and deduct cost from account cash balance."""
    entry_dt = entry_date or datetime.now(timezone.utc)
    position = PortfolioPosition(
        account_id=account_id,
        ticker=ticker.upper(),
        archetype=archetype,
        conviction_score=conviction_score,
        status="OPEN",
        shares=shares,
        entry_date=entry_dt,
        entry_price=entry_price,
        current_price=entry_price,
        stop_loss_price=stop_loss_price,
        target_price=target_price,
        holding_days=0,
        unrealized_pnl=0.0,
        return_pct=0.0,
        spy_entry_price=spy_entry_price,
    )
    db.add(position)

    # Deduct cost from account cash
    cost = round(shares * entry_price, 2)
    account = await db.get(PortfolioAccount, account_id)
    if account:
        account.cash_balance = round(account.cash_balance - cost, 2)
        account.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(position)
    return position


async def get_open_positions(
    db: AsyncSession, account_id: int | None = None
) -> list[PortfolioPosition]:
    """Retrieve all active open positions for an account."""
    query = select(PortfolioPosition).where(PortfolioPosition.status == "OPEN")
    if account_id is not None:
        query = query.where(PortfolioPosition.account_id == account_id)
    query = query.order_by(desc(PortfolioPosition.entry_date))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_closed_positions(
    db: AsyncSession, account_id: int | None = None, limit: int = 100
) -> list[PortfolioPosition]:
    """Retrieve closed historical positions for trade journal."""
    query = select(PortfolioPosition).where(PortfolioPosition.status == "CLOSED")
    if account_id is not None:
        query = query.where(PortfolioPosition.account_id == account_id)
    query = query.order_by(desc(PortfolioPosition.exit_date)).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_position_by_id(
    db: AsyncSession, position_id: int
) -> PortfolioPosition | None:
    """Retrieve a single portfolio position by ID."""
    return await db.get(PortfolioPosition, position_id)


async def update_open_position_price(
    db: AsyncSession,
    position: PortfolioPosition,
    current_price: float,
    holding_days: int | None = None,
) -> PortfolioPosition:
    """Update mark-to-market current price and unrealized PnL for an open position."""
    position.current_price = round(current_price, 2)
    if position.entry_price and position.entry_price > 0:
        position.unrealized_pnl = round((position.current_price - position.entry_price) * position.shares, 2)
        position.return_pct = round(((position.current_price - position.entry_price) / position.entry_price) * 100.0, 2)
    if holding_days is not None:
        position.holding_days = holding_days
    position.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(position)
    return position


async def close_portfolio_position(
    db: AsyncSession,
    position: PortfolioPosition,
    exit_price: float,
    exit_reason: str,
    exit_date: datetime | None = None,
    spy_exit_price: float | None = None,
) -> PortfolioPosition:
    """Close an open position, calculate realized PnL and SPY alpha, and credit proceeds to account."""
    exit_dt = exit_date or datetime.now(timezone.utc)
    proceeds = round(position.shares * exit_price, 2)
    cost = round(position.shares * position.entry_price, 2)

    position.status = "CLOSED"
    position.exit_price = round(exit_price, 2)
    position.current_price = round(exit_price, 2)
    position.exit_date = exit_dt
    position.exit_reason = exit_reason
    position.realized_pnl = round(proceeds - cost, 2)
    position.unrealized_pnl = 0.0

    if position.entry_price and position.entry_price > 0:
        position.return_pct = round(((exit_price - position.entry_price) / position.entry_price) * 100.0, 2)
    else:
        position.return_pct = 0.0

    # Calculate SPY benchmark return and excess alpha
    if spy_exit_price is not None:
        position.spy_exit_price = round(spy_exit_price, 2)
    if position.spy_entry_price and position.spy_exit_price and position.spy_entry_price > 0:
        position.spy_return_pct = round(((position.spy_exit_price - position.spy_entry_price) / position.spy_entry_price) * 100.0, 2)
        position.excess_alpha_pct = round(position.return_pct - position.spy_return_pct, 2)

    # Calculate final holding days if entry_date and exit_date exist
    if position.entry_date and exit_dt:
        days = (exit_dt.date() - position.entry_date.date()).days
        position.holding_days = max(1, days)

    position.updated_at = datetime.now(timezone.utc)

    # Return proceeds to account cash
    account = await db.get(PortfolioAccount, position.account_id)
    if account:
        account.cash_balance = round(account.cash_balance + proceeds, 2)
        account.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(position)
    return position


async def save_portfolio_snapshot(
    db: AsyncSession,
    account_id: int,
    snapshot_date: datetime,
    cash_balance: float,
    invested_capital: float,
    total_equity: float,
    portfolio_return_pct: float,
    spy_price: float | None = None,
    spy_return_pct: float | None = None,
    excess_alpha_pct: float | None = None,
    open_positions_count: int = 0,
) -> PortfolioSnapshot:
    """Save a daily equity curve snapshot for the portfolio."""
    snapshot = PortfolioSnapshot(
        account_id=account_id,
        snapshot_date=snapshot_date,
        cash_balance=round(cash_balance, 2),
        invested_capital=round(invested_capital, 2),
        total_equity=round(total_equity, 2),
        portfolio_return_pct=round(portfolio_return_pct, 2),
        spy_price=round(spy_price, 2) if spy_price is not None else None,
        spy_return_pct=round(spy_return_pct, 2) if spy_return_pct is not None else None,
        excess_alpha_pct=round(excess_alpha_pct, 2) if excess_alpha_pct is not None else None,
        open_positions_count=open_positions_count,
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def get_portfolio_snapshots(
    db: AsyncSession, account_id: int | None = None, limit: int = 180
) -> list[PortfolioSnapshot]:
    """Retrieve chronological portfolio equity snapshots for charting."""
    query = select(PortfolioSnapshot)
    if account_id is not None:
        query = query.where(PortfolioSnapshot.account_id == account_id)
    query = query.order_by(PortfolioSnapshot.snapshot_date.asc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_latest_portfolio_snapshot(
    db: AsyncSession, account_id: int | None = None
) -> PortfolioSnapshot | None:
    """Retrieve the most recent portfolio snapshot."""
    query = select(PortfolioSnapshot)
    if account_id is not None:
        query = query.where(PortfolioSnapshot.account_id == account_id)
    query = query.order_by(desc(PortfolioSnapshot.snapshot_date)).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()

