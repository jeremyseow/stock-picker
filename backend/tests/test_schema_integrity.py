"""Permanent relational schema integrity guardrails.

Prevents domain leakage, raw/leaderboard duplication inside report tables,
and silent-discard ORM __init__ shims from creeping back into app/models.py
or drifting out of sync with backend/stock_analyzer.db.
"""
import os
import sqlite3
import pytest

from app.database import Base
from app.models import (
    CoreEquityReport,
    RetailSentimentReport,
    SmartMoneyReport,
    OptionsWhaleRaw,
    OptionsWhaleReport,
    SynthesisReport,
)


def _table_columns(table_name: str) -> set[str]:
    assert table_name in Base.metadata.tables, f"Missing table {table_name}"
    return set(Base.metadata.tables[table_name].columns.keys())


def test_core_equity_report_single_owner_columns():
    cols = _table_columns("core_equity_reports")
    assert "core_raw_id" in cols
    forbidden = {"raw_metrics", "raw_news", "raw_filings"}
    assert forbidden.isdisjoint(cols), f"Forbidden raw columns on core_equity_reports: {cols & forbidden}"


def test_retail_sentiment_report_single_owner_columns():
    cols = _table_columns("retail_sentiment_reports")
    assert {"core_intel_id", "daily_ticker_id"}.issubset(cols)
    forbidden = {
        # Leaderboard columns owned by daily_tickers
        "rank",
        "mention_count",
        "engagement_score",
        # Insider / smart money columns owned by Engine 2
        "smart_money_verdict",
        "raw_insider_data",
        # Core intel columns owned by core_equity_reports
        "company_name",
        "sector",
        "industry",
        "current_price",
        "target_price",
        "ground_truth_status",
        "ground_truth_filings_news",
        "events_happenings",
        "reconciliation_risk_score",
        "reconciliation_analysis",
    }
    assert forbidden.isdisjoint(cols), f"Forbidden columns on retail_sentiment_reports: {cols & forbidden}"


def test_smart_money_report_single_owner_columns():
    cols = _table_columns("smart_money_reports")
    assert {"core_intel_id", "smart_money_ticker_id"}.issubset(cols)
    forbidden = {
        # Leaderboard columns owned by smart_money_tickers
        "rank",
        "conviction_score",
        "cluster_count",
        "total_buy_volume",
        "top_buyer_summary",
        # Core intel columns owned by core_equity_reports
        "company_name",
        "sector",
        "industry",
        "current_price",
        "target_price",
        "market_cap",
        "pe_ratio",
        "forward_pe",
        "fifty_two_week_high",
        "fifty_two_week_low",
        "ground_truth_status",
        "ground_truth_filings_news",
        "events_happenings",
        "risk_score",
    }
    assert forbidden.isdisjoint(cols), f"Forbidden columns on smart_money_reports: {cols & forbidden}"


def test_options_whale_single_owner_columns():
    raw_cols = _table_columns("options_whale_raw")
    assert {"dte", "is_otm", "is_sweep"}.issubset(raw_cols)
    assert "options_report_id" not in raw_cols, "Layer 1 options_whale_raw must not hold a FK to Layer 2 reports"

    # Also enforce across ALL Layer 1 _raw tables: zero FKs pointing to Layer 2 tables
    layer2_tables = {
        "core_equity_reports",
        "retail_sentiment_reports",
        "smart_money_reports",
        "options_whale_reports",
        "synthesis_reports",
    }
    for raw_table_name in (
        "core_equity_raw",
        "retail_social_raw",
        "insider_trades_raw",
        "congress_trades_raw",
        "options_whale_raw",
    ):
        for fk in Base.metadata.tables[raw_table_name].foreign_keys:
            assert fk.column.table.name not in layer2_tables, (
                f"Layer 1 table '{raw_table_name}' must not depend on Layer 2 '{fk.column.table.name}'"
            )

    junction_cols = _table_columns("options_report_contracts")
    assert {"options_report_id", "options_raw_id"} == junction_cols

    rep_cols = _table_columns("options_whale_reports")
    assert {"core_intel_id", "options_whale_ticker_id"}.issubset(rep_cols)
    forbidden = {
        # Leaderboard columns owned by options_whale_tickers
        "rank",
        "whale_score",
        "unusual_oi_multiplier",
        "put_call_ratio",
        "net_bullish_premium",
        "top_strike_summary",
        # Contract list owned by options_whale_raw
        "unusual_contracts",
        # Core intel columns owned by core_equity_reports
        "company_name",
        "sector",
        "industry",
        "current_price",
        "target_price",
    }
    assert forbidden.isdisjoint(cols := rep_cols), f"Forbidden columns on options_whale_reports: {cols & forbidden}"


def test_synthesis_report_single_owner_columns():
    cols = _table_columns("synthesis_reports")
    assert {
        "core_intel_id",
        "retail_report_id",
        "smart_money_report_id",
        "options_whale_report_id",
    }.issubset(cols)
    forbidden = {
        "retail_rank",
        "retail_mentions",
        "retail_sentiment",
        "smart_money_rank",
        "smart_money_conviction",
        "whale_options_score",
        "put_call_ratio",
    }
    assert forbidden.isdisjoint(cols), f"Forbidden snapshot columns on synthesis_reports: {cols & forbidden}"


def test_no_silent_discard_orm_init_shims():
    """Passing removed or arbitrary unknown kwargs must fail loudly rather than being silently discarded."""
    for cls in (
        CoreEquityReport,
        RetailSentimentReport,
        SmartMoneyReport,
        OptionsWhaleReport,
        SynthesisReport,
    ):
        with pytest.raises(TypeError):
            cls(ticker="AAPL", __invalid_kwarg_guard__=True)

    with pytest.raises((TypeError, AttributeError)):
        CoreEquityReport(ticker="AAPL", raw_metrics={"pe": 10})
    with pytest.raises((TypeError, AttributeError)):
        RetailSentimentReport(ticker="AAPL", smart_money_verdict="Bullish")
    with pytest.raises((TypeError, AttributeError)):
        RetailSentimentReport(ticker="AAPL", rank=1)
    with pytest.raises((TypeError, AttributeError)):
        SmartMoneyReport(ticker="AAPL", cluster_count=3)
    with pytest.raises((TypeError, AttributeError)):
        OptionsWhaleRaw(ticker="AAPL", options_report_id=1)
    with pytest.raises((TypeError, AttributeError)):
        OptionsWhaleReport(ticker="AAPL", whale_score=90.0)
    with pytest.raises((TypeError, AttributeError)):
        OptionsWhaleReport(ticker="AAPL", unusual_contracts=[])
    with pytest.raises((TypeError, AttributeError)):
        SynthesisReport(ticker="AAPL", retail_mentions=50)


def test_live_sqlite_schema_parity():
    """Verify backend/stock_analyzer.db matches Base.metadata.tables column-for-column."""
    db_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "stock_analyzer.db")
    )
    if not os.path.exists(db_path):
        pytest.skip("backend/stock_analyzer.db not present in workspace")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        db_tables = {row[0] for row in cur.fetchall() if not row[0].startswith("sqlite_")}
        expected_tables = set(Base.metadata.tables.keys())
        missing_tables = expected_tables - db_tables
        assert not missing_tables, f"Tables missing in live SQLite DB: {missing_tables}"

        for table_name in sorted(expected_tables):
            cur.execute(f"PRAGMA table_info('{table_name}')")
            actual_cols = {row[1] for row in cur.fetchall()}
            expected_cols = _table_columns(table_name)
            assert actual_cols == expected_cols, (
                f"Schema drift on '{table_name}': "
                f"extra={actual_cols - expected_cols}, missing={expected_cols - actual_cols}"
            )

        cur.execute("PRAGMA foreign_key_check")
        fk_errors = cur.fetchall()
        assert not fk_errors, f"Foreign key integrity violations in live SQLite DB: {fk_errors}"
    finally:
        conn.close()

