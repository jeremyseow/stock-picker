import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.smart_money_scorer import (
    get_role_weight,
    get_cluster_multiplier,
    score_insider_trades,
    score_congressional_trades,
    rank_smart_money_candidates,
)
from app.synthesis_engine import generate_cross_engine_synthesis
from app.models import (
    DailyTicker,
    TickerReport,
    SmartMoneyTicker,
)


def test_role_weight_hierarchy():
    assert get_role_weight("Chief Executive Officer") == 3.0
    assert get_role_weight("CEO") == 3.0
    assert get_role_weight("CFO") == 3.0
    assert get_role_weight("Chairman") == 3.0
    assert get_role_weight("Director") == 2.0
    assert get_role_weight("10% Owner") == 2.0
    assert get_role_weight("VP of Sales") == 1.0
    assert get_role_weight("General Counsel") == 1.0


def test_cluster_multiplier_scaling():
    assert get_cluster_multiplier(1) == 1.0
    assert get_cluster_multiplier(2) == 1.5
    assert get_cluster_multiplier(3) == 2.5
    assert get_cluster_multiplier(5) == 2.5


def test_score_insider_trades_calculation():
    mock_trades = [
        {
            "ticker": "NVDA",
            "insider_name": "Jensen Huang",
            "title": "CEO",
            "value": 500000.0,
            "delta_own": 0.25,
        },
        {
            "ticker": "NVDA",
            "insider_name": "Colette Kress",
            "title": "CFO",
            "value": 250000.0,
            "delta_own": 0.10,
        },
    ]

    scores = score_insider_trades(mock_trades)
    assert "NVDA" in scores
    nvda = scores["NVDA"]
    assert nvda["cluster_count"] == 2
    assert nvda["total_buy_volume"] == 750000.0
    # Base: 750k / 50k = 15.0 * 3.0 (CEO) * 1.5 (2 buyers) * 1.25 (growth) = 84.38
    assert nvda["insider_score"] > 50.0


def test_score_congressional_trades():
    mock_congress = [
        {
            "ticker": "LMT",
            "politician": "Rep. Michael McCaul",
            "amount_range": "$100,001 - $250,000",
        }
    ]
    scores = score_congressional_trades(mock_congress)
    assert "LMT" in scores
    assert scores["LMT"]["political_score"] > 0.0


@patch("app.smart_money_scorer.is_valid_ticker")
def test_rank_smart_money_candidates(mock_valid):
    mock_valid.return_value = True

    insiders = [
        {"ticker": "AAPL", "insider_name": "Cook", "title": "CEO", "value": 1000000.0, "delta_own": 0.5},
        {"ticker": "MSFT", "insider_name": "Satya", "title": "CEO", "value": 50000.0, "delta_own": 0.05},
    ]
    congress = [
        {"ticker": "AAPL", "politician": "Sen. Pelosi", "amount_range": "$500,001 - $1,000,000"}
    ]

    ranked = rank_smart_money_candidates(insiders, congress, limit=2)
    assert len(ranked) == 2
    # AAPL should rank #1 due to larger buy volume and Congressional trade
    assert ranked[0]["ticker"] == "AAPL"
    assert ranked[1]["ticker"] == "MSFT"


@pytest.mark.asyncio
async def test_synthesis_archetype_classification():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    mock_db = AsyncMock()

    # Mock Engine 1 tickers (AAPL has retail hype, LMT has 0 retail hype)
    mock_e1_ticker = DailyTicker(ticker="AAPL", date=now, rank=1, mention_count=45, engagement_score=2500.0)
    mock_e1_rep = TickerReport(
        ticker="AAPL",
        date=now,
        community_sentiment="85% Bullish",
        smart_money_verdict="Bullish Accumulation",
        recommendation="BUY"
    )

    # Mock Engine 2 tickers (LMT has high smart money conviction, AAPL has smart money)
    mock_e2_aapl = SmartMoneyTicker(ticker="AAPL", date=now, rank=1, conviction_score=65.0, cluster_count=3, top_buyer_summary="CEO, 2 Dirs")
    mock_e2_lmt = SmartMoneyTicker(ticker="LMT", date=now, rank=2, conviction_score=55.0, cluster_count=2, top_buyer_summary="Rep. McCaul, Dir Smith")

    # Mock DB query results
    async def mock_execute(query):
        q_str = str(query).lower()
        mock_res = MagicMock()
        if "max(daily_tickers.date)" in q_str:
            mock_res.scalar_one_or_none.return_value = now
        elif "from daily_tickers" in q_str:
            mock_res.scalars().all.return_value = [mock_e1_ticker]
        elif "from ticker_reports" in q_str:
            mock_res.scalar_one_or_none.return_value = mock_e1_rep
        elif "max(smart_money_tickers.date)" in q_str:
            mock_res.scalar_one_or_none.return_value = now
        elif "from smart_money_tickers" in q_str:
            mock_res.scalars().all.return_value = [mock_e2_aapl, mock_e2_lmt]
        else:
            mock_res.scalars().all.return_value = []
            mock_res.scalar_one_or_none.return_value = None
        return mock_res

    mock_db.execute.side_effect = mock_execute
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()

    results = await generate_cross_engine_synthesis(mock_db)

    # AAPL has both high retail and high smart money -> The Rocket
    aapl_res = next((r for r in results if r["ticker"] == "AAPL"), None)
    assert aapl_res is not None
    assert aapl_res["archetype"] == "The Rocket"
    assert aapl_res["recommended_action"] == "STRONG BUY"

    # LMT has 0 retail mentions and high smart money -> Silent Accumulation
    lmt_res = next((r for r in results if r["ticker"] == "LMT"), None)
    assert lmt_res is not None
    assert lmt_res["archetype"] == "Silent Accumulation"
    assert lmt_res["recommended_action"] == "EARLY SWING BUY"
    assert lmt_res["retail_awareness_level"] == "Zero Awareness (Stealth)"
    assert lmt_res["timing_edge_score"] == 95.0


@pytest.mark.asyncio
async def test_get_latest_synthesis_records_deduplication():
    from app.crud import get_latest_synthesis_records
    from app.models import SynthesisRecord
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    mock_db = AsyncMock()
    
    # Simulate multiple runs within window having duplicate tickers
    rec1 = SynthesisRecord(id=1, ticker="AAPL", date=now, timing_edge_score=95.0, archetype="The Rocket")
    rec2 = SynthesisRecord(id=2, ticker="AAPL", date=now - timedelta(seconds=2), timing_edge_score=90.0, archetype="The Rocket")
    rec3 = SynthesisRecord(id=3, ticker="MSFT", date=now, timing_edge_score=80.0, archetype="Silent Accumulation")
    
    async def mock_exec(query):
        mock_res = MagicMock()
        q_str = str(query).lower()
        if "max(synthesis_records.date)" in q_str:
            mock_res.scalar_one_or_none.return_value = now
        elif "from synthesis_records" in q_str:
            mock_res.scalars().all.return_value = [rec1, rec2, rec3]
        return mock_res

    mock_db.execute.side_effect = mock_exec

    results = await get_latest_synthesis_records(mock_db)
    assert len(results) == 2
    tickers = [r.ticker for r in results]
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    assert len(set(tickers)) == 2
