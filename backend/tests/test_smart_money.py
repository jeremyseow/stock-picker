import pytest
import pytest_asyncio
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import (
    RetailSentimentReport,
    CoreEquityRaw,
    CoreEquityReport,
    InsiderTradesRaw,
    CongressTradesRaw,
)
from app.main import app
from app.llm_schemas import RetailOverlayAnalysis
from app.market_researcher import fetch_insider_data, fetch_congressional_trades
from app.agent import SYSTEM_PROMPT


def test_retail_overlay_schema_excludes_insider_fields():
    """Verify Engine 1 RetailOverlayAnalysis has zero Form 4 / Congressional insider fields."""
    report = RetailOverlayAnalysis(
        community_sentiment="80% Bullish",
        community_hype="Hype around new product launch",
        reconciliation_actionable_insight="Monitor retail flow.",
        recommendation="BUY",
        recommendation_rationale="Strong fundamentals and alignment.",
    )
    assert report.recommendation == "BUY"
    assert not hasattr(report, "smart_money_verdict")
    assert not hasattr(report, "insider_activity_summary")


def test_agent_system_prompt_excludes_insider_instructions():
    """Verify Engine 1 SYSTEM_PROMPT focuses on Core Intel + Retail and excludes Form 4/Congress rules."""
    assert "smart_money_verdict" not in SYSTEM_PROMPT
    assert "insider_activity_summary" not in SYSTEM_PROMPT
    assert "SEC Form 4" not in SYSTEM_PROMPT


def test_fetch_insider_data_with_mock_yfinance():
    """Verify fetch_insider_data correctly parses 6m metrics and Form 4 transactions."""
    mock_ticker = MagicMock()

    # Mock purchases DataFrame with substantial accumulation (>50,000 net shares)
    mock_ticker.insider_purchases = pd.DataFrame([
        {"Insider Purchases Last 6m": "Purchases", "Shares": 120000.0, "Trans": 4},
        {"Insider Purchases Last 6m": "Sales", "Shares": 20000.0, "Trans": 2},
        {"Insider Purchases Last 6m": "Net Shares Purchased (Sold)", "Shares": 100000.0, "Trans": None},
        {"Insider Purchases Last 6m": "Total Insider Shares Held", "Shares": 500000.0, "Trans": None},
    ])

    # Mock transactions DataFrame
    mock_ticker.insider_transactions = pd.DataFrame([
        {
            "Start Date": "2026-10-15",
            "Insider": "Jane Doe",
            "Position": "Chief Executive Officer",
            "Shares": 10000,
            "Value": 2500000,
            "Text": "Purchase at price $250.00",
            "Ownership": "D"
        },
        {
            "Start Date": "2026-10-10",
            "Insider": "John Smith",
            "Position": "Chief Financial Officer",
            "Shares": 2000,
            "Value": 500000,
            "Text": "Sale at price $250.00",
            "Ownership": "D"
        }
    ])

    with patch("yfinance.Ticker", return_value=mock_ticker):
        data = fetch_insider_data("TEST")

    assert data["has_data"] is True
    assert data["purchases_shares"] == 120000.0
    assert data["purchases_trans"] == 4
    assert data["sales_shares"] == 20000.0
    assert data["sales_trans"] == 2
    assert data["net_shares"] == 100000.0
    assert "Accumulation" in data["sentiment_label"]
    assert len(data["recent_transactions"]) == 2
    assert data["recent_transactions"][0]["insider"] == "Jane Doe"
    assert data["recent_transactions"][0]["type"] == "BUY"
    assert data["recent_transactions"][0]["price"] == "$250.00"
    assert data["recent_transactions"][0]["details"] == "Purchase"
    assert data["recent_transactions"][1]["insider"] == "John Smith"
    assert data["recent_transactions"][1]["type"] == "SELL"
    assert data["recent_transactions"][1]["price"] == "$250.00"
    assert data["recent_transactions"][1]["details"] == "Sale"


def test_fetch_insider_data_handles_nan_and_missing_values():
    """Verify fetch_insider_data gracefully handles float NaN, None, and <NA> in yfinance DataFrames."""
    import numpy as np

    mock_ticker = MagicMock()
    mock_ticker.insider_purchases = pd.DataFrame([
        {"Insider Purchases Last 6m": "Purchases", "Shares": 50000.0, "Trans": 3},
        {"Insider Purchases Last 6m": "Sales", "Shares": np.nan, "Trans": float("nan")},
        {"Insider Purchases Last 6m": "Net Shares Purchased (Sold)", "Shares": 50000.0, "Trans": pd.NA},
        {"Insider Purchases Last 6m": "Total Insider Shares Held", "Shares": np.nan, "Trans": None},
    ])
    mock_ticker.insider_transactions = pd.DataFrame([
        {
            "Start Date": "2026-08-14",
            "Insider": "Kumar Neil",
            "Position": "Chief Executive Officer",
            "Shares": 71217,
            "Value": np.nan,  # Reproduces BBIO NaN error
            "Text": None,
            "Ownership": np.nan,
        },
        {
            "Start Date": pd.NaT,
            "Insider": np.nan,
            "Position": np.nan,
            "Shares": float("nan"),
            "Value": 100000,
            "Text": "Purchase at price $10.00",
            "Ownership": "D",
        }
    ])

    with patch("yfinance.Ticker", return_value=mock_ticker):
        data = fetch_insider_data("BBIO")

    assert data["has_data"] is True
    assert data["purchases_shares"] == 50000.0
    assert data["sales_shares"] == 0.0
    assert len(data["recent_transactions"]) == 2
    # Row 1 with NaN value
    assert data["recent_transactions"][0]["shares"] == 71217
    assert data["recent_transactions"][0]["value"] == 0
    assert data["recent_transactions"][0]["price"] == "-"
    assert data["recent_transactions"][0]["ownership"] == "D"
    # Row 2 with NaT date, NaN insider/shares
    assert data["recent_transactions"][1]["date"] == "Unknown"
    assert data["recent_transactions"][1]["insider"] == "Unknown"
    assert data["recent_transactions"][1]["shares"] == 0
    assert data["recent_transactions"][1]["value"] == 100000


def test_fetch_insider_data_empty_fallback():
    """Verify fallback when yfinance returns empty or None DataFrames."""
    mock_ticker = MagicMock()
    mock_ticker.insider_purchases = None
    mock_ticker.insider_transactions = None

    with patch("yfinance.Ticker", return_value=mock_ticker):
        data = fetch_insider_data("NONE")

    assert data["has_data"] is False
    assert data["purchases_shares"] == 0.0
    assert data["recent_transactions"] == []


def test_fetch_congressional_trades_mock():
    """Verify fetch_congressional_trades handles DDGS search hits."""
    mock_results = [
        {"title": "Senator Smith Discloses Stock Purchase in XYZ", "href": "https://example.com/trade1", "body": "Filed Form A disclosing purchase."},
        {"title": "Representative Jones Sales Disclosure", "href": "https://example.com/trade2", "body": "Sold 500 shares under STOCK Act."}
    ]

    with patch("app.market_researcher.DDGS") as mock_ddgs_cls:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value = mock_instance
        mock_instance.text.return_value = mock_results
        mock_ddgs_cls.return_value = mock_instance

        trades = fetch_congressional_trades("XYZ")

    assert len(trades) == 2
    assert trades[0]["title"] == "Senator Smith Discloses Stock Purchase in XYZ"
    assert trades[0]["link"] == "https://example.com/trade1"


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def smart_money_test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        ts = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
        core_raw = CoreEquityRaw(
            ticker="TSLA",
            captured_at=ts,
            raw_metrics={"industry": "Automotive", "sector": "Consumer Cyclical"},
        )
        session.add(core_raw)
        await session.flush()

        core = CoreEquityReport(
            ticker="TSLA",
            date=ts,
            core_raw_id=core_raw.id,
            sector="Consumer Cyclical",
            industry="Automotive",
            current_price=250.0,
            target_price=220.0,
            ground_truth_status="Automotive margins declining",
            ground_truth_filings_news="10-Q shows shrinking automotive gross margins",
            events_happenings="Robotaxi reveal event",
            risk_score="High",
            risk_analysis="Heavy insider liquidation into retail meme pump.",
            actionable_insight="Trim or hedge long positions.",
        )
        session.add(core)
        await session.flush()

        rep = RetailSentimentReport(
            ticker="TSLA",
            date=ts,
            core_intel_id=core.id,
            community_sentiment="90% Bullish",
            community_hype="Extreme retail euphoria",
            reconciliation_actionable_insight="Trim or hedge long positions.",
            recommendation="SELL",
            recommendation_rationale="C-suite dumping shares despite retail optimism.",
        )
        insider = InsiderTradesRaw(
            ticker="TSLA",
            captured_at=ts,
            filing_date="2026-10-25",
            trade_date="2026-10-25",
            insider_name="Elon Executive",
            position="CEO",
            transaction_type="SELL",
            shares=50000.0,
            total_value=12500000.0,
            price="$250.00",
        )
        congress = CongressTradesRaw(
            ticker="TSLA",
            captured_at=ts,
            politician_name="Representative Jones",
            transaction_type="Sale",
            amount_range="$15,001 - $50,000",
            snippet="Sold 500 shares under STOCK Act.",
            source_url="https://example.com/capitol",
        )
        session.add_all([rep, insider, congress])
        await session.commit()

    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_api_serves_smart_money_data(smart_money_test_db):
    """Test /api/master/report/{ticker} builds insider payload from Engine 2 while /api/retail/reports stays pure Engine 1."""
    async_session = async_sessionmaker(smart_money_test_db, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Fetch individual master report (combines Engine 1 + Engine 2 insider data)
        resp = await ac.get("/api/master/report/TSLA")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "TSLA"
        assert "Bearish" in data["smart_money_verdict"] or "Selling" in data["smart_money_verdict"]
        assert data["raw_insider_data"]["has_data"] is True
        assert data["raw_insider_data"]["net_shares"] == -50000.0
        assert len(data["raw_insider_data"]["congressional_trades"]) == 1
        assert len(data["raw_insider_data"]["recent_transactions"]) == 1
        assert len(data["smart_money_overlay"]["outflow_ledger"]) == 1

        # 2. Fetch list of retail reports (verdict derived from Engine 2, no raw_insider_data leak)
        list_resp = await ac.get("/api/retail/reports?date=2026-10-30")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 1
        assert items[0]["ticker"] == "TSLA"
        assert "raw_insider_data" not in items[0]
        assert "Selling" in items[0]["smart_money_verdict"] or "Bearish" in items[0]["smart_money_verdict"]

    app.dependency_overrides.clear()
