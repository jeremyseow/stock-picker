from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text
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
    option_type = Column(String, nullable=True)  # CALL, PUT
    volume = Column(Integer, default=0)
    open_interest = Column(Integer, default=0)
    volume_oi_ratio = Column(Float, default=0.0)
    spot_price = Column(Float, nullable=True)
    premium_spent = Column(Float, default=0.0)
    sentiment = Column(String, nullable=True)


# ==========================================
# Layer 2: Synthesized Reports & Intelligence (_reports)
# ==========================================

class CoreEquityReport(Base):
    """
    Shared foundational equity research record across discovery engines.
    Single source of truth for fundamentals, SEC 10-Q/8-K ground truth, corporate news, and risks.
    """
    __tablename__ = "core_equity_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

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

    raw_metrics = Column(JSON, nullable=True)
    raw_news = Column(JSON, nullable=True)
    raw_filings = Column(JSON, nullable=True)


class RetailSentimentReport(Base):
    """
    Engine 1 specialized overlay: Retail sentiment, hype narrative, and conservative recommendation.
    Links to CoreEquityReport for fundamental grounding.
    """
    __tablename__ = "retail_sentiment_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)

    rank = Column(Integer, nullable=True)
    mention_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)

    community_sentiment = Column(String, nullable=True)
    community_hype = Column(String, nullable=True)

    recommendation = Column(String, nullable=True)  # BUY, SELL, HOLD
    recommendation_rationale = Column(String, nullable=True)
    reconciliation_actionable_insight = Column(String, nullable=True)
    smart_money_verdict = Column(String, nullable=True)
    raw_insider_data = Column(JSON, nullable=True)

    # Relational link to single source of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")

    def __init__(self, **kwargs):
        # Absorb normalized fields if passed by callers/fixtures
        self._current_price = kwargs.pop("current_price", None)
        self._target_price = kwargs.pop("target_price", None)
        self._ground_truth_status = kwargs.pop("ground_truth_status", None)
        self._ground_truth_filings_news = kwargs.pop("ground_truth_filings_news", None)
        self._events_happenings = kwargs.pop("events_happenings", None)
        self._risk_score = kwargs.pop("reconciliation_risk_score", kwargs.pop("risk_score", None))
        self._risk_analysis = kwargs.pop("reconciliation_analysis", kwargs.pop("risk_analysis", None))
        self._raw_metrics = kwargs.pop("raw_metrics", None)
        self._raw_news = kwargs.pop("raw_news", None)
        super().__init__(**kwargs)

    # Transparent property proxies for backward-compatibility
    @property
    def current_price(self):
        if self.core_intel and self.core_intel.current_price is not None:
            return self.core_intel.current_price
        return getattr(self, "_current_price", None)

    @property
    def target_price(self):
        if self.core_intel and self.core_intel.target_price is not None:
            return self.core_intel.target_price
        return getattr(self, "_target_price", None)

    @property
    def ground_truth_status(self):
        if self.core_intel and self.core_intel.ground_truth_status is not None:
            return self.core_intel.ground_truth_status
        return getattr(self, "_ground_truth_status", None)

    @property
    def ground_truth_filings_news(self):
        if self.core_intel and self.core_intel.ground_truth_filings_news is not None:
            return self.core_intel.ground_truth_filings_news
        return getattr(self, "_ground_truth_filings_news", None)

    @property
    def events_happenings(self):
        if self.core_intel and self.core_intel.events_happenings is not None:
            return self.core_intel.events_happenings
        return getattr(self, "_events_happenings", None)

    @property
    def reconciliation_risk_score(self):
        if self.core_intel and self.core_intel.risk_score is not None:
            return self.core_intel.risk_score
        return getattr(self, "_risk_score", None)

    @property
    def reconciliation_analysis(self):
        if self.core_intel and self.core_intel.risk_analysis is not None:
            return self.core_intel.risk_analysis
        return getattr(self, "_risk_analysis", None)

    @property
    def raw_metrics(self):
        if self.core_intel and self.core_intel.raw_metrics is not None:
            return self.core_intel.raw_metrics
        return getattr(self, "_raw_metrics", {})

    @property
    def raw_news(self):
        if self.core_intel and self.core_intel.raw_news is not None:
            return self.core_intel.raw_news
        return getattr(self, "_raw_news", [])


class SmartMoneyReport(Base):
    """
    Engine 2 specialized overlay: Form 4 inflow ledger, committee jurisdiction, and swing catalyst horizon.
    Links to CoreEquityReport for fundamental grounding.
    """
    __tablename__ = "smart_money_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)

    rank = Column(Integer, nullable=True)
    conviction_score = Column(Float, default=0.0)
    conviction_tier = Column(String, nullable=True)
    cluster_count = Column(Integer, default=0)
    total_buy_volume = Column(Float, default=0.0)
    top_buyer_summary = Column(String, nullable=True)
    inflow_ledger = Column(JSON, nullable=True)

    political_catalyst_analysis = Column(String, nullable=True)
    corporate_catalyst_analysis = Column(String, nullable=True)
    catalyst_horizon = Column(String, nullable=True)
    actionable_thesis = Column(String, nullable=True)

    # Relational link to single source of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")

    def __init__(self, **kwargs):
        self._company_name = kwargs.pop("company_name", None)
        self._sector = kwargs.pop("sector", None)
        self._industry = kwargs.pop("industry", None)
        self._current_price = kwargs.pop("current_price", None)
        self._target_price = kwargs.pop("target_price", None)
        self._ground_truth_status = kwargs.pop("ground_truth_status", None)
        self._ground_truth_filings_news = kwargs.pop("ground_truth_filings_news", None)
        self._events_happenings = kwargs.pop("events_happenings", None)
        self._risk_score = kwargs.pop("risk_score", None)
        self._raw_metrics = kwargs.pop("raw_metrics", None)
        super().__init__(**kwargs)

    # Transparent property proxies for backward-compatibility
    @property
    def company_name(self):
        if self.core_intel and self.core_intel.company_name is not None:
            return self.core_intel.company_name
        return getattr(self, "_company_name", self.ticker)

    @property
    def sector(self):
        if self.core_intel and self.core_intel.sector is not None:
            return self.core_intel.sector
        return getattr(self, "_sector", "General")

    @property
    def industry(self):
        if self.core_intel and self.core_intel.industry is not None:
            return self.core_intel.industry
        return getattr(self, "_industry", "General")

    @property
    def current_price(self):
        if self.core_intel and self.core_intel.current_price is not None:
            return self.core_intel.current_price
        return getattr(self, "_current_price", None)

    @property
    def target_price(self):
        if self.core_intel and self.core_intel.target_price is not None:
            return self.core_intel.target_price
        return getattr(self, "_target_price", None)

    @property
    def ground_truth_status(self):
        if self.core_intel and self.core_intel.ground_truth_status is not None:
            return self.core_intel.ground_truth_status
        return getattr(self, "_ground_truth_status", None)

    @property
    def ground_truth_filings_news(self):
        if self.core_intel and self.core_intel.ground_truth_filings_news is not None:
            return self.core_intel.ground_truth_filings_news
        return getattr(self, "_ground_truth_filings_news", None)

    @property
    def events_happenings(self):
        if self.core_intel and self.core_intel.events_happenings is not None:
            return self.core_intel.events_happenings
        return getattr(self, "_events_happenings", None)

    @property
    def risk_score(self):
        if self.core_intel and self.core_intel.risk_score is not None:
            return self.core_intel.risk_score
        return getattr(self, "_risk_score", None)

    @property
    def raw_metrics(self):
        if self.core_intel and self.core_intel.raw_metrics is not None:
            return self.core_intel.raw_metrics
        return getattr(self, "_raw_metrics", {})


class OptionsWhaleReport(Base):
    """
    Engine 3 specialized overlay: Unusual volume-to-open-interest options sweeps, 
    put/call skews, and institutional sentiment.
    Links to CoreEquityReport for fundamental grounding.
    """
    __tablename__ = "options_whale_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)

    rank = Column(Integer, nullable=True)
    whale_score = Column(Float, default=0.0)
    unusual_oi_multiplier = Column(Float, default=1.0)
    put_call_ratio = Column(Float, default=1.0)
    net_bullish_premium = Column(Float, default=0.0)
    sentiment_bias = Column(String, nullable=True)  # "Extremely Bullish", "Bullish Sweeps", "Cautious / Put Skew"
    top_strike_summary = Column(String, nullable=True)
    unusual_contracts = Column(JSON, nullable=True)

    # Relational link to single source of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")

    def __init__(self, **kwargs):
        self._company_name = kwargs.pop("company_name", None)
        self._sector = kwargs.pop("sector", None)
        self._industry = kwargs.pop("industry", None)
        self._current_price = kwargs.pop("current_price", None)
        self._target_price = kwargs.pop("target_price", None)
        self._ground_truth_status = kwargs.pop("ground_truth_status", None)
        self._ground_truth_filings_news = kwargs.pop("ground_truth_filings_news", None)
        self._events_happenings = kwargs.pop("events_happenings", None)
        self._risk_score = kwargs.pop("risk_score", None)
        self._raw_metrics = kwargs.pop("raw_metrics", None)
        super().__init__(**kwargs)

    # Transparent property proxies for backward-compatibility
    @property
    def company_name(self):
        if self.core_intel and self.core_intel.company_name is not None:
            return self.core_intel.company_name
        return getattr(self, "_company_name", self.ticker)

    @property
    def sector(self):
        if self.core_intel and self.core_intel.sector is not None:
            return self.core_intel.sector
        return getattr(self, "_sector", "General")

    @property
    def industry(self):
        if self.core_intel and self.core_intel.industry is not None:
            return self.core_intel.industry
        return getattr(self, "_industry", "General")

    @property
    def current_price(self):
        if self.core_intel and self.core_intel.current_price is not None:
            return self.core_intel.current_price
        return getattr(self, "_current_price", None)

    @property
    def target_price(self):
        if self.core_intel and self.core_intel.target_price is not None:
            return self.core_intel.target_price
        return getattr(self, "_target_price", None)

    @property
    def ground_truth_status(self):
        if self.core_intel and self.core_intel.ground_truth_status is not None:
            return self.core_intel.ground_truth_status
        return getattr(self, "_ground_truth_status", None)

    @property
    def ground_truth_filings_news(self):
        if self.core_intel and self.core_intel.ground_truth_filings_news is not None:
            return self.core_intel.ground_truth_filings_news
        return getattr(self, "_ground_truth_filings_news", None)

    @property
    def events_happenings(self):
        if self.core_intel and self.core_intel.events_happenings is not None:
            return self.core_intel.events_happenings
        return getattr(self, "_events_happenings", None)

    @property
    def risk_score(self):
        if self.core_intel and self.core_intel.risk_score is not None:
            return self.core_intel.risk_score
        return getattr(self, "_risk_score", None)

    @property
    def raw_metrics(self):
        if self.core_intel and self.core_intel.raw_metrics is not None:
            return self.core_intel.raw_metrics
        return getattr(self, "_raw_metrics", {})


class SynthesisReport(Base):
    """Cross-engine synthesis mapping a stock into market divergence archetypes."""
    __tablename__ = "synthesis_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_reports.id"), nullable=True, index=True)

    archetype = Column(String)  # The Rocket, The Retail Trap, Silent Accumulation, Market Noise
    retail_rank = Column(Integer, nullable=True)
    retail_mentions = Column(Integer, default=0)
    retail_sentiment = Column(String, nullable=True)

    smart_money_rank = Column(Integer, nullable=True)
    smart_money_conviction = Column(Float, default=0.0)
    smart_money_flow = Column(String, nullable=True)

    retail_awareness_level = Column(String)  # Zero Awareness (Stealth), Emerging, Saturated Hype
    timing_edge_score = Column(Float)        # 0.0 to 100.0
    synthesis_diagnosis = Column(String)
    recommended_action = Column(String)     # STRONG BUY, AVOID/SHORT, EARLY SWING BUY, PASS

    # Engine 3 options flow signals (nullable for backward compatibility)
    whale_options_flow = Column(String, nullable=True)
    whale_options_score = Column(Float, default=0.0)
    put_call_ratio = Column(Float, nullable=True)

    # Relational link to single source of truth
    core_intel = relationship("CoreEquityReport", foreign_keys=[core_intel_id], lazy="selectin")


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

