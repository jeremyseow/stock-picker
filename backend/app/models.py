from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


# ==========================================
# Discovery / Candidate Tickers
# ==========================================

class DailyTicker(Base):
    __tablename__ = "daily_tickers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ticker = Column(String, index=True)
    rank = Column(Integer)
    mention_count = Column(Integer)
    engagement_score = Column(Float)


class SmartMoneyTicker(Base):
    """Represents a top-ranked ticker identified by Engine 2 (Smart Money Scout)."""
    __tablename__ = "smart_money_tickers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ticker = Column(String, index=True)
    rank = Column(Integer)
    conviction_score = Column(Float)
    insider_score = Column(Float)
    political_score = Column(Float)
    cluster_count = Column(Integer, default=0)
    total_buy_volume = Column(Float, default=0.0)
    top_buyer_summary = Column(String)


class OptionsWhaleTicker(Base):
    """Represents a top-ranked ticker identified by Engine 3 (Institutional Whale Options Radar)."""
    __tablename__ = "options_whale_tickers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ticker = Column(String, index=True)
    rank = Column(Integer)
    whale_score = Column(Float)
    unusual_oi_multiplier = Column(Float)
    net_bullish_premium = Column(Float, default=0.0)
    put_call_ratio = Column(Float, default=1.0)
    top_strike_summary = Column(String, nullable=True)


# ==========================================
# Layer 1: Raw Audit & Ingestion Tables (_raw)
# ==========================================

class CoreEquityRaw(Base):
    """Raw ingestion data for equity fundamentals, SEC filings, and news."""
    __tablename__ = "core_equity_raw"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)

    raw_metrics = Column(JSON, nullable=True)
    raw_news = Column(JSON, nullable=True)
    raw_filings = Column(JSON, nullable=True)


class RetailSocialRaw(Base):
    """Raw social media posts, comments, and sentiment mentions."""
    __tablename__ = "retail_social_raw"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    platform = Column(String, default="reddit")
    post_id = Column(String, nullable=True)
    subreddit = Column(String, nullable=True)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    score = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    post_url = Column(String, nullable=True)
    post_body = Column(Text, nullable=True)


class InsiderTradesRaw(Base):
    """Individual Form 4 insider transactions (both Buys and Sells)."""
    __tablename__ = "insider_trades_raw"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    filing_date = Column(String, nullable=True, index=True)
    trade_date = Column(String, nullable=True)
    insider_name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False, index=True)  # BUY, SELL, OTHER
    shares = Column(Float, nullable=True)
    price = Column(String, nullable=True)
    total_value = Column(Float, default=0.0)
    ownership = Column(String, nullable=True)
    filing_details = Column(String, nullable=True)


class CongressTradesRaw(Base):
    """Individual STOCK Act congressional trade disclosures (Buys, Sells, Trackers)."""
    __tablename__ = "congress_trades_raw"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    filing_date = Column(String, nullable=True, index=True)
    trade_date = Column(String, nullable=True)
    politician_name = Column(String, nullable=False)
    chamber = Column(String, nullable=True)
    party = Column(String, nullable=True)
    committee = Column(String, nullable=True)
    transaction_type = Column(String, default="BUY")
    amount_range = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)


class OptionsWhaleRaw(Base):
    """Raw unusual options sweep contracts and volume/OI data."""
    __tablename__ = "options_whale_raw"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    timestamp = Column(String, nullable=True)
    strike = Column(Float, nullable=True)
    expiry_date = Column(String, nullable=True)
    dte = Column(Integer, nullable=True)
    option_type = Column(String, nullable=True)  # CALL, PUT
    volume = Column(Integer, default=0)
    open_interest = Column(Integer, default=0)
    volume_oi_ratio = Column(Float, default=0.0)
    spot_price = Column(Float, nullable=True)
    premium_spent = Column(Float, default=0.0)
    sentiment = Column(String, nullable=True)
    is_otm = Column(Boolean, nullable=True)
    is_sweep = Column(Boolean, nullable=True)


# ==========================================
# Layer 2: Synthesized Reports & Intelligence (_reports)
# ==========================================

class CoreEquityReport(Base):
    """
    Shared foundational equity research record across discovery engines.
    Single source of truth for fundamentals, SEC 10-Q/8-K ground truth, corporate news, and risks.
    Raw JSON payloads (raw_metrics, raw_news, raw_filings) live strictly on CoreEquityRaw.
    """
    __tablename__ = "core_equity_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_raw_id = Column(Integer, ForeignKey("core_equity_raw.id"), nullable=True, index=True)

    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)

    ground_truth_status = Column(String, nullable=True)
    ground_truth_filings_news = Column(String, nullable=True)
    events_happenings = Column(String, nullable=True)

    risk_score = Column(String, nullable=True)  # Low, Medium, High
    risk_analysis = Column(String, nullable=True)
    actionable_insight = Column(String, nullable=True)

    core_raw = relationship("CoreEquityRaw", foreign_keys=[core_raw_id], lazy="selectin")

    @property
    def raw_metrics(self):
        return (self.core_raw.raw_metrics if self.core_raw else None) or {}

    @property
    def raw_news(self):
        return (self.core_raw.raw_news if self.core_raw else None) or []

    @property
    def raw_filings(self):
        return (self.core_raw.raw_filings if self.core_raw else None) or []


class RetailSentimentReport(Base):
    """
    Engine 1 specialized overlay: Retail sentiment, hype narrative, and conservative recommendation.
    Links to CoreEquityReport for fundamental grounding and DailyTicker for social leaderboard metrics.
    Does NOT own Engine 2 insider/Congressional columns.
    """
    __tablename__ = "retail_sentiment_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)
    daily_ticker_id = Column(Integer, ForeignKey("daily_tickers.id"), nullable=True, index=True)

    community_sentiment = Column(String, nullable=True)
    community_hype = Column(String, nullable=True)

    recommendation = Column(String, nullable=True)  # BUY, SELL, HOLD
    recommendation_rationale = Column(String, nullable=True)
    reconciliation_actionable_insight = Column(String, nullable=True)

    # Relational links to single sources of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")
    daily_ticker = relationship("DailyTicker", foreign_keys=[daily_ticker_id], lazy="selectin")

    @property
    def rank(self):
        return self.daily_ticker.rank if self.daily_ticker else None

    @property
    def mention_count(self):
        return self.daily_ticker.mention_count if self.daily_ticker else 0

    @property
    def engagement_score(self):
        return self.daily_ticker.engagement_score if self.daily_ticker else 0.0

    @property
    def company_name(self):
        return self.core_intel.company_name if self.core_intel else self.ticker

    @property
    def sector(self):
        return self.core_intel.sector if self.core_intel else "General"

    @property
    def industry(self):
        return self.core_intel.industry if self.core_intel else "General"

    @property
    def current_price(self):
        return self.core_intel.current_price if self.core_intel else None

    @property
    def target_price(self):
        return self.core_intel.target_price if self.core_intel else None

    @property
    def ground_truth_status(self):
        return self.core_intel.ground_truth_status if self.core_intel else None

    @property
    def ground_truth_filings_news(self):
        return self.core_intel.ground_truth_filings_news if self.core_intel else None

    @property
    def events_happenings(self):
        return self.core_intel.events_happenings if self.core_intel else None

    @property
    def reconciliation_risk_score(self):
        return self.core_intel.risk_score if self.core_intel else None

    @property
    def reconciliation_analysis(self):
        return self.core_intel.risk_analysis if self.core_intel else None

    @property
    def raw_metrics(self):
        return self.core_intel.raw_metrics if self.core_intel else {}

    @property
    def raw_news(self):
        return self.core_intel.raw_news if self.core_intel else []


class SmartMoneyReport(Base):
    """
    Engine 2 specialized overlay: Form 4 inflow ledger, committee jurisdiction, and swing catalyst horizon.
    Links to CoreEquityReport for fundamental grounding and SmartMoneyTicker for leaderboard scores.
    """
    __tablename__ = "smart_money_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)
    smart_money_ticker_id = Column(Integer, ForeignKey("smart_money_tickers.id"), nullable=True, index=True)

    conviction_tier = Column(String, nullable=True)
    inflow_ledger = Column(JSON, nullable=True)

    political_catalyst_analysis = Column(String, nullable=True)
    corporate_catalyst_analysis = Column(String, nullable=True)
    catalyst_horizon = Column(String, nullable=True)
    actionable_thesis = Column(String, nullable=True)

    # Relational links to single sources of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")
    smart_money_ticker = relationship("SmartMoneyTicker", foreign_keys=[smart_money_ticker_id], lazy="selectin")

    @property
    def rank(self):
        return self.smart_money_ticker.rank if self.smart_money_ticker else None

    @property
    def conviction_score(self):
        return self.smart_money_ticker.conviction_score if self.smart_money_ticker else 0.0

    @property
    def insider_score(self):
        return self.smart_money_ticker.insider_score if self.smart_money_ticker else 0.0

    @property
    def political_score(self):
        return self.smart_money_ticker.political_score if self.smart_money_ticker else 0.0

    @property
    def cluster_count(self):
        return self.smart_money_ticker.cluster_count if self.smart_money_ticker else 0

    @property
    def total_buy_volume(self):
        return self.smart_money_ticker.total_buy_volume if self.smart_money_ticker else 0.0

    @property
    def top_buyer_summary(self):
        return self.smart_money_ticker.top_buyer_summary if self.smart_money_ticker else ""

    @property
    def company_name(self):
        return self.core_intel.company_name if self.core_intel else self.ticker

    @property
    def sector(self):
        return self.core_intel.sector if self.core_intel else "General"

    @property
    def industry(self):
        return self.core_intel.industry if self.core_intel else "General"

    @property
    def current_price(self):
        return self.core_intel.current_price if self.core_intel else None

    @property
    def target_price(self):
        return self.core_intel.target_price if self.core_intel else None

    @property
    def ground_truth_status(self):
        return self.core_intel.ground_truth_status if self.core_intel else None

    @property
    def ground_truth_filings_news(self):
        return self.core_intel.ground_truth_filings_news if self.core_intel else None

    @property
    def events_happenings(self):
        return self.core_intel.events_happenings if self.core_intel else None

    @property
    def risk_score(self):
        return self.core_intel.risk_score if self.core_intel else None

    @property
    def raw_metrics(self):
        return self.core_intel.raw_metrics if self.core_intel else {}


options_report_contracts = Table(
    "options_report_contracts",
    Base.metadata,
    Column(
        "options_report_id",
        Integer,
        ForeignKey("options_whale_reports.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "options_raw_id",
        Integer,
        ForeignKey("options_whale_raw.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class OptionsWhaleReport(Base):
    """
    Engine 3 specialized overlay: Institutional sentiment bias for unusual options flow.
    Links to CoreEquityReport for fundamentals, OptionsWhaleTicker for scores,
    and OptionsWhaleRaw (via options_report_contracts) for unusual contract details.
    """
    __tablename__ = "options_whale_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)
    options_whale_ticker_id = Column(Integer, ForeignKey("options_whale_tickers.id"), nullable=True, index=True)

    sentiment_bias = Column(String, nullable=True)  # "Extremely Bullish", "Bullish Sweeps", "Cautious / Put Skew"

    # Relational links to single sources of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")
    options_whale_ticker = relationship("OptionsWhaleTicker", foreign_keys=[options_whale_ticker_id], lazy="selectin")
    raw_contracts = relationship(
        "OptionsWhaleRaw",
        secondary=options_report_contracts,
        lazy="selectin",
        order_by="desc(OptionsWhaleRaw.premium_spent)",
    )

    @property
    def rank(self):
        return self.options_whale_ticker.rank if self.options_whale_ticker else None

    @property
    def whale_score(self):
        return self.options_whale_ticker.whale_score if self.options_whale_ticker else 0.0

    @property
    def unusual_oi_multiplier(self):
        return self.options_whale_ticker.unusual_oi_multiplier if self.options_whale_ticker else 1.0

    @property
    def put_call_ratio(self):
        return self.options_whale_ticker.put_call_ratio if self.options_whale_ticker else 1.0

    @property
    def net_bullish_premium(self):
        return self.options_whale_ticker.net_bullish_premium if self.options_whale_ticker else 0.0

    @property
    def top_strike_summary(self):
        return self.options_whale_ticker.top_strike_summary if self.options_whale_ticker else ""

    @property
    def unusual_contracts(self):
        return [
            {
                "type": c.option_type,
                "strike": c.strike,
                "expiration": c.expiry_date,
                "dte": c.dte,
                "volume": c.volume,
                "open_interest": c.open_interest,
                "ratio": c.volume_oi_ratio,
                "spot": c.spot_price,
                "premium": c.premium_spent,
                "sentiment": c.sentiment,
                "is_otm": c.is_otm,
                "is_sweep": c.is_sweep,
            }
            for c in (self.raw_contracts or [])
        ]

    @property
    def company_name(self):
        return self.core_intel.company_name if self.core_intel else self.ticker

    @property
    def sector(self):
        return self.core_intel.sector if self.core_intel else "General"

    @property
    def industry(self):
        return self.core_intel.industry if self.core_intel else "General"

    @property
    def current_price(self):
        return self.core_intel.current_price if self.core_intel else None

    @property
    def target_price(self):
        return self.core_intel.target_price if self.core_intel else None

    @property
    def ground_truth_status(self):
        return self.core_intel.ground_truth_status if self.core_intel else None

    @property
    def ground_truth_filings_news(self):
        return self.core_intel.ground_truth_filings_news if self.core_intel else None

    @property
    def events_happenings(self):
        return self.core_intel.events_happenings if self.core_intel else None

    @property
    def risk_score(self):
        return self.core_intel.risk_score if self.core_intel else None

    @property
    def raw_metrics(self):
        return self.core_intel.raw_metrics if self.core_intel else {}


class SynthesisReport(Base):
    """
    Cross-engine synthesis mapping a stock into market divergence archetypes.
    Links directly to CoreEquityReport and the 3 Engine report tables instead of duplicating their metrics.
    """
    __tablename__ = "synthesis_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)
    retail_report_id = Column(Integer, ForeignKey("retail_sentiment_reports.id"), nullable=True, index=True)
    smart_money_report_id = Column(Integer, ForeignKey("smart_money_reports.id"), nullable=True, index=True)
    options_whale_report_id = Column(Integer, ForeignKey("options_whale_reports.id"), nullable=True, index=True)

    archetype = Column(String)  # The Rocket, The Retail Trap, Silent Accumulation, Market Noise
    smart_money_flow = Column(String, nullable=True)  # Synthesized flow label (clusters or Form 4 sells)
    whale_options_flow = Column(String, nullable=True)  # Synthesized options flow label

    retail_awareness_level = Column(String)  # Zero Awareness (Stealth), Emerging, Saturated Hype
    timing_edge_score = Column(Float)        # 0.0 to 100.0
    synthesis_diagnosis = Column(String)
    recommended_action = Column(String)     # STRONG BUY, AVOID/SHORT, EARLY SWING BUY, PASS

    # Relational links to single sources of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")
    retail_report = relationship("RetailSentimentReport", foreign_keys=[retail_report_id], lazy="selectin")
    smart_money_report = relationship("SmartMoneyReport", foreign_keys=[smart_money_report_id], lazy="selectin")
    options_whale_report = relationship("OptionsWhaleReport", foreign_keys=[options_whale_report_id], lazy="selectin")

    @property
    def retail_rank(self):
        return self.retail_report.rank if self.retail_report else None

    @property
    def retail_mentions(self):
        return self.retail_report.mention_count if self.retail_report else 0

    @property
    def retail_sentiment(self):
        return self.retail_report.community_sentiment if self.retail_report else "Unmonitored"

    @property
    def smart_money_rank(self):
        return self.smart_money_report.rank if self.smart_money_report else None

    @property
    def smart_money_conviction(self):
        return self.smart_money_report.conviction_score if self.smart_money_report else 0.0

    @property
    def whale_options_score(self):
        return self.options_whale_report.whale_score if self.options_whale_report else 0.0

    @property
    def put_call_ratio(self):
        return self.options_whale_report.put_call_ratio if self.options_whale_report else None


# ==========================================
# Analytics & Trajectory
# ==========================================

class TickerTrajectoryAnalysis(Base):
    __tablename__ = "ticker_trajectory_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    latest_report_id = Column(Integer, index=True)
    report_count = Column(Integer)
    divergence_analysis = Column(String)
    catalyst_follow_through = Column(String)
    trajectory_outlook = Column(String)


class ModelCalibrationRun(Base):
    """Stores historical backtest scorecards and timestamped weight calibrations."""
    __tablename__ = "model_calibration_runs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    sample_runs_count = Column(Integer, default=0)
    overall_hit_rate_t30 = Column(Float, default=0.0)
    avg_alpha_vs_spy_t30 = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    archetype_scorecard = Column(JSON, nullable=True)
    active_weights = Column(JSON, nullable=False)
    recommended_weights = Column(JSON, nullable=True)
    is_applied = Column(Integer, default=0)  # 1 if applied to active configuration
    scorecard_data = Column(JSON, nullable=True)


# ==========================================
# Paper Trading Portfolio Ledger
# ==========================================

class PortfolioAccount(Base):
    """Primary ledger account for simulated paper trading."""
    __tablename__ = "portfolio_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Primary Fund")
    initial_balance = Column(Float, default=100000.0)
    cash_balance = Column(Float, default=100000.0)
    total_equity = Column(Float, default=100000.0)
    max_positions = Column(Integer, default=10)
    allocation_per_trade = Column(Float, default=10000.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    positions = relationship("PortfolioPosition", back_populates="account", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="account", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    """Tracks active and historical simulated positions with trade exit execution."""
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("portfolio_accounts.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    archetype = Column(String, nullable=False)
    conviction_score = Column(Float, default=0.0)
    status = Column(String, default="OPEN", index=True)  # OPEN or CLOSED
    shares = Column(Integer, nullable=False)
    entry_date = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    stop_loss_price = Column(Float, nullable=False)
    exit_date = Column(DateTime, nullable=True, index=True)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)  # STOP_LOSS, TAKE_PROFIT, TIME_EXIT, MANUAL
    realized_pnl = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)
    holding_days = Column(Integer, default=0)
    spy_entry_price = Column(Float, nullable=True)
    spy_exit_price = Column(Float, nullable=True)
    spy_return_pct = Column(Float, nullable=True)
    excess_alpha_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    account = relationship("PortfolioAccount", back_populates="positions")


class PortfolioSnapshot(Base):
    """Daily equity curve snapshots and market benchmark comparisons."""
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("portfolio_accounts.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    cash_balance = Column(Float, nullable=False)
    invested_capital = Column(Float, nullable=False)
    total_equity = Column(Float, nullable=False)
    portfolio_return_pct = Column(Float, default=0.0)
    spy_price = Column(Float, nullable=True)
    spy_return_pct = Column(Float, nullable=True)
    excess_alpha_pct = Column(Float, nullable=True)
    open_positions_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    account = relationship("PortfolioAccount", back_populates="snapshots")

