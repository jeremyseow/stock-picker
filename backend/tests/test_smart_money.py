import pytest
import pytest_asyncio
import pandas as pd
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database import Base, get_db
from app.models import TickerReport
from app.main import app
from app.llm_schemas import StockReport
from app.market_researcher import fetch_insider_data, fetch_congressional_trades
from app.agent import SYSTEM_PROMPT


def test_stock_report_schema_smart_money_defaults():
    """Verify StockReport defaults and serialization with smart money fields."""
    report = StockReport(
        recommendation="BUY",
        recommendation_rationale="Strong fundamentals and alignment.",
        community_sentiment="80% Bullish",
        community_hype="Hype around new product launch",
        ground_truth_status="Solid balance sheet",
        ground_truth_filings_news="10-K confirmed revenue growth",
        events_happenings="Investor day showcase",
        smart_money_verdict="Bullish Accumulation",
        insider_activity_summary="Insiders purchased 50,000 shares with zero C-suite sales.",
        reconciliation_risk_score="Low",
        reconciliation_analysis="Both retail and insiders are accumulating.",
        reconciliation_actionable_insight="Establish long position."
    )
    assert report.smart_money_verdict == "Bullish Accumulation"
    assert "50,000 shares" in report.insider_activity_summary


def test_agent_system_prompt_guardrails():
    """Verify that system prompt enforces smart money rules blocking BUY on heavy insider sales."""
    assert "smart_money_verdict" in SYSTEM_PROMPT
    assert "insider_activity_summary" in SYSTEM_PROMPT
    assert "SEC Form 4 disclosures DO NOT show heavy net insider selling" in SYSTEM_PROMPT


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
    assert data["recent_transactions"][1]["insider"] == "John Smith"
    assert data["recent_transactions"][1]["type"] == "SELL"


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
        rep = TickerReport(
            ticker="TSLA",
            date=datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc),
            current_price=250.0,
            target_price=220.0,
            community_sentiment="90% Bullish",
            community_hype="Extreme retail euphoria",
            ground_truth_status="Automotive margins declining",
            ground_truth_filings_news="10-Q shows shrinking automotive gross margins",
            events_happenings="Robotaxi reveal event",
            smart_money_verdict="Bearish Divergence",
            raw_insider_data={
                "has_data": True,
                "purchases_shares": 0.0,
                "sales_shares": 50000.0,
                "net_shares": -50000.0,
                "sentiment_label": "Bearish / Net Selling",
                "insider_activity_summary": "Executives dumping shares into retail rally.",
                "congressional_trades": [
                    {
                        "title": "Representative Jones Sales Disclosure",
                        "link": "https://example.com/capitol",
                        "snippet": "Sold 500 shares under STOCK Act."
                    }
                ],
                "recent_transactions": [
                    {
                        "date": "2026-10-25",
                        "insider": "Elon Executive",
                        "position": "CEO",
                        "shares": 50000,
                        "value": 12500000,
                        "text": "Sale at price $250.00",
                        "type": "SELL",
                        "ownership": "D"
                    }
                ]
            },
            reconciliation_risk_score="High",
            reconciliation_analysis="Heavy insider liquidation into retail meme pump.",
            reconciliation_actionable_insight="Trim or hedge long positions.",
            recommendation="SELL",
            recommendation_rationale="C-suite dumping shares despite retail optimism.",
            raw_metrics={"industry": "Automotive", "sector": "Consumer Cyclical"}
        )
        session.add(rep)
        await session.commit()

    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_api_serves_smart_money_data(smart_money_test_db):
    """Test /api/reports/{ticker} and /api/reports return smart_money_verdict and raw_insider_data."""
    async_session = async_sessionmaker(smart_money_test_db, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Fetch individual report
        resp = await ac.get("/api/reports/TSLA")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "TSLA"
        assert data["smart_money_verdict"] == "Bearish Divergence"
        assert data["raw_insider_data"]["has_data"] is True
        assert data["raw_insider_data"]["net_shares"] == -50000.0
        assert data["raw_insider_data"]["insider_activity_summary"] == "Executives dumping shares into retail rally."
        assert len(data["raw_insider_data"]["congressional_trades"]) == 1
        assert len(data["raw_insider_data"]["recent_transactions"]) == 1

        # 2. Fetch list of reports
        list_resp = await ac.get("/api/reports?date=2026-10-30")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 1
        assert items[0]["ticker"] == "TSLA"
        assert items[0]["smart_money_verdict"] == "Bearish Divergence"

    app.dependency_overrides.clear()
