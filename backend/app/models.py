from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from app.database import Base


class DailyTicker(Base):
    __tablename__ = "daily_tickers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ticker = Column(String, index=True)
    rank = Column(Integer)
    mention_count = Column(Integer)
    engagement_score = Column(Float)


class CoreEquityIntel(Base):
    """
    Shared foundational equity research record across both discovery engines.
    Stores financial ratios, SEC 10-Q/8-K analyses, corporate news, and Gemini ground truth synthesis.
    """
    __tablename__ = "core_equity_intels"

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


class RetailReport(Base):
    """
    Engine 1 specialized overlay: Retail sentiment, hype narrative, and conservative recommendation.
    Links to CoreEquityIntel for fundamental grounding.
    """
    __tablename__ = "retail_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_intels.id"), nullable=True, index=True)

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

    # Denormalized convenience fields populated from CoreEquityIntel
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)
    ground_truth_status = Column(String, nullable=True)
    ground_truth_filings_news = Column(String, nullable=True)
    events_happenings = Column(String, nullable=True)
    reconciliation_risk_score = Column(String, nullable=True)
    reconciliation_analysis = Column(String, nullable=True)
    raw_metrics = Column(JSON, nullable=True)
    raw_news = Column(JSON, nullable=True)


# Backward-compatibility alias
TickerReport = RetailReport


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


class SmartMoneyReport(Base):
    """
    Engine 2 specialized overlay: Form 4 inflow ledger, committee jurisdiction, and swing catalyst horizon.
    Links to CoreEquityIntel for fundamental grounding.
    """
    __tablename__ = "smart_money_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_intels.id"), nullable=True, index=True)

    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)

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

    # Denormalized convenience fields populated from CoreEquityIntel
    ground_truth_status = Column(String, nullable=True)
    ground_truth_filings_news = Column(String, nullable=True)
    events_happenings = Column(String, nullable=True)
    risk_score = Column(String, nullable=True)
    raw_metrics = Column(JSON, nullable=True)


class SynthesisRecord(Base):
    """Cross-engine synthesis mapping a stock into market divergence archetypes."""
    __tablename__ = "synthesis_records"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_intels.id"), nullable=True, index=True)

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


class OptionsWhaleReport(Base):
    """
    Engine 3 specialized overlay: Unusual volume-to-open-interest options sweeps, 
    put/call skews, and institutional sentiment.
    Links to CoreEquityIntel for fundamental grounding.
    """
    __tablename__ = "options_whale_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    core_intel_id = Column(Integer, ForeignKey("core_equity_intels.id"), nullable=True, index=True)

    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    target_price = Column(Float, nullable=True)

    rank = Column(Integer, nullable=True)
    whale_score = Column(Float, default=0.0)
    unusual_oi_multiplier = Column(Float, default=1.0)
    put_call_ratio = Column(Float, default=1.0)
    net_bullish_premium = Column(Float, default=0.0)
    sentiment_bias = Column(String, nullable=True)  # "Extremely Bullish", "Bullish Sweeps", "Cautious / Put Skew"
    top_strike_summary = Column(String, nullable=True)
    unusual_contracts = Column(JSON, nullable=True)

    # Denormalized convenience fields populated from CoreEquityIntel
    ground_truth_status = Column(String, nullable=True)
    ground_truth_filings_news = Column(String, nullable=True)
    events_happenings = Column(String, nullable=True)
    risk_score = Column(String, nullable=True)
    raw_metrics = Column(JSON, nullable=True)


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

