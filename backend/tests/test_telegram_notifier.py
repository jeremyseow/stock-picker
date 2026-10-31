import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from app.telegram_notifier import (
    get_recommendation_badge,
    get_smart_money_badge,
    format_daily_digest,
    send_daily_digest
)


def test_recommendation_badges():
    """Verify recommendation badge formatting with emoji indicators."""
    assert "🟢" in get_recommendation_badge("BUY")
    assert "<b>BUY</b>" in get_recommendation_badge("BUY")
    assert "🔴" in get_recommendation_badge("SELL")
    assert "🟡" in get_recommendation_badge("HOLD")
    assert "⚪" in get_recommendation_badge(None)


def test_smart_money_badges():
    """Verify smart money verdict badges."""
    assert "📋" in get_smart_money_badge("No Form 4 Filings")
    assert "🔴" in get_smart_money_badge("Bearish Divergence: C-Suite Selling")
    assert "🟢" in get_smart_money_badge("Bullish Accumulation")
    assert "⚖️" in get_smart_money_badge("Neutral Flow")
    assert "⚖️" in get_smart_money_badge(None)


def test_format_daily_digest():
    """Verify complete HTML digest formatting and calculations."""
    mock_reports = [
        {
            "rank": 1,
            "ticker": "NVDA",
            "recommendation": "BUY",
            "current_price": 100.0,
            "target_price": 150.0,
            "smart_money_verdict": "Bullish Accumulation",
            "actionable_insight": "Track upcoming Blackwell GPU shipments and cloud revenue."
        },
        {
            "rank": 2,
            "ticker": "TSLA",
            "recommendation": "HOLD",
            "current_price": 200.0,
            "target_price": 180.0,
            "smart_money_verdict": "Bearish Divergence",
            "actionable_insight": "A" * 200  # Verify truncation
        }
    ]

    fixed_date = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
    digest = format_daily_digest(mock_reports, run_date=fixed_date)

    assert "<b>Antigravity StockPicker — Daily Digest</b>" in digest
    assert "Oct 31, 2026" in digest
    assert "#1 $NVDA" in digest
    assert "🟢 <b>BUY</b>" in digest
    assert "$100.00 ➔ Target: $150.00 (+50.0%)" in digest
    assert "🟢 Bullish Accumulation" in digest
    assert "#2 $TSLA" in digest
    assert "$200.00 ➔ Target: $180.00 (-10.0%)" in digest
    # Check truncation
    assert "..." in digest


@pytest.mark.asyncio
async def test_send_daily_digest_missing_env_skipped():
    """Verify notification is gracefully skipped when credentials are not configured."""
    with patch.dict("os.environ", {}, clear=True):
        res = await send_daily_digest([{"ticker": "AAPL"}], bot_token=None, chat_id=None)
        assert res is False


@pytest.mark.asyncio
async def test_send_daily_digest_empty_reports():
    """Verify notification is skipped when report list is empty."""
    res = await send_daily_digest([], bot_token="token", chat_id="123")
    assert res is False


@pytest.mark.asyncio
async def test_send_daily_digest_success():
    """Verify successful dispatch over httpx."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    mock_reports = [
        {
            "rank": 1,
            "ticker": "AAPL",
            "recommendation": "BUY",
            "current_price": 220.0,
            "target_price": 250.0,
            "smart_money_verdict": "Bullish",
            "actionable_insight": "Monitor iPhone demand."
        }
    ]

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await send_daily_digest(
            mock_reports,
            bot_token="test_token",
            chat_id="test_chat_id"
        )

        assert success is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["chat_id"] == "test_chat_id"
        assert call_kwargs["json"]["parse_mode"] == "HTML"
        assert "AAPL" in call_kwargs["json"]["text"]


@pytest.mark.asyncio
async def test_send_daily_digest_http_error_handled():
    """Verify HTTP errors do not raise exceptions."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Request: chat not found"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await send_daily_digest(
            [{"ticker": "AAPL"}],
            bot_token="test_token",
            chat_id="invalid_chat_id"
        )
        assert success is False


@pytest.mark.asyncio
async def test_send_daily_digest_network_exception_handled():
    """Verify network timeouts or exceptions do not crash the caller."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectTimeout("Network timed out")
        success = await send_daily_digest(
            [{"ticker": "AAPL"}],
            bot_token="test_token",
            chat_id="test_chat_id"
        )
        assert success is False

