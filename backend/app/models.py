from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
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
    
class TickerReport(Base):
    __tablename__ = "ticker_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    current_price = Column(Float)
    target_price = Column(Float)
    
    community_sentiment = Column(String)
    community_hype = Column(String)
    
    ground_truth_status = Column(String)
    ground_truth_filings_news = Column(String)
    events_happenings = Column(String)
    
    smart_money_verdict = Column(String)
    raw_insider_data = Column(JSON)
    
    reconciliation_risk_score = Column(String)
    reconciliation_analysis = Column(String)
    reconciliation_actionable_insight = Column(String)
    
    recommendation = Column(String) # BUY, SELL, HOLD
    recommendation_rationale = Column(String)
    raw_metrics = Column(JSON)
    raw_news = Column(JSON)

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
    """Detailed catalyst and macro research report for an Engine 2 candidate."""
    __tablename__ = "smart_money_reports"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    company_name = Column(String)
    sector = Column(String)
    industry = Column(String)
    current_price = Column(Float)
    target_price = Column(Float)

    conviction_score = Column(Float)
    conviction_tier = Column(String)  # High Conviction Catalyst Buy, Speculative Accumulation, etc.
    inflow_ledger = Column(JSON)      # List of individual insider & Congressional transactions

    political_catalyst_analysis = Column(String)
    corporate_catalyst_analysis = Column(String)
    catalyst_horizon = Column(String)  # e.g. "45-75 days until NDAA markup"
    actionable_thesis = Column(String)
    raw_metrics = Column(JSON)


class SynthesisRecord(Base):
    """Cross-engine synthesis mapping a stock into market divergence archetypes."""
    __tablename__ = "synthesis_records"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

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

