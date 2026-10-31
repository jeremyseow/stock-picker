import os
import html
import logging
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)


def get_recommendation_badge(rec: str | None) -> str:
    """Return formatted recommendation label with emoji badge."""
    rec_upper = (rec or "").upper()
    if rec_upper == "BUY":
        return "🟢 <b>BUY</b>"
    elif rec_upper == "SELL":
        return "🔴 <b>SELL</b>"
    elif rec_upper == "HOLD":
        return "🟡 <b>HOLD</b>"
    return "⚪ <b>NO REPORT</b>"


def get_smart_money_badge(verdict: str | None) -> str:
    """Return formatted smart money verdict with contextual emoji indicator."""
    if not verdict:
        return "⚖️ Neutral"
    v_clean = html.escape(verdict)
    text = verdict.lower()
    if "no form 4" in text or "no data" in text:
        return f"📋 {v_clean}"
    if "bearish" in text or "selling" in text or "divergence" in text:
        return f"🔴 {v_clean}"
    if "bullish" in text or "accumulation" in text or "buying" in text:
        return f"🟢 {v_clean}"
    return f"⚖️ {v_clean}"


def format_daily_digest(reports: list[dict], run_date: datetime | None = None) -> str:
    """
    Formats a list of ticker report summaries into a clean Telegram HTML message.
    Each item in reports should contain:
      - rank: int
      - ticker: str
      - recommendation: str
      - current_price: float | None
      - target_price: float | None
      - smart_money_verdict: str | None
      - actionable_insight: str | None
    """
    dt_str = (run_date or datetime.now(timezone.utc)).strftime("%b %d, %Y")
    lines = [
        "📊 <b>Antigravity StockPicker — Daily Digest</b>",
        f"📅 <i>{dt_str} • {len(reports)} Tickers Analyzed</i>",
        ""
    ]

    for item in reports:
        rank = item.get("rank", 1)
        ticker = html.escape(item.get("ticker", "UNKNOWN"))
        rec = item.get("recommendation", "HOLD")
        rec_badge = get_recommendation_badge(rec)

        current_price = item.get("current_price")
        target_price = item.get("target_price")

        price_str = f"${current_price:.2f}" if current_price is not None else "N/A"
        if target_price is not None:
            if current_price and current_price > 0:
                upside = ((target_price - current_price) / current_price) * 100
                upside_sign = "+" if upside >= 0 else ""
                price_str += f" ➔ Target: ${target_price:.2f} ({upside_sign}{upside:.1f}%)"
            else:
                price_str += f" ➔ Target: ${target_price:.2f}"

        smart_money = get_smart_money_badge(item.get("smart_money_verdict"))
        raw_insight = item.get("actionable_insight") or item.get("reconciliation_actionable_insight") or ""
        insight = html.escape(raw_insight.strip())
        if len(insight) > 160:
            insight = insight[:157] + "..."

        lines.append(f"<b>#{rank} ${ticker}</b> — {rec_badge}")
        lines.append(f"• Price: <code>{price_str}</code>")
        lines.append(f"• Smart Money: {smart_money}")
        if insight:
            lines.append(f"• Insight: <i>{insight}</i>")
        lines.append("")

    lines.append("⚡ <i>Scraped from r/wallstreetbets • Powered by Gemini 2.5 Pro</i>")
    return "\n".join(lines).strip()


async def send_daily_digest(
    reports: list[dict],
    bot_token: str | None = None,
    chat_id: str | None = None,
    timeout: float = 10.0
) -> bool:
    """
    Transmits the formatted digest to the configured Telegram chat.
    Returns True if successfully sent, False otherwise.
    Never raises exceptions that could disrupt pipeline execution.
    """
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat:
        logger.info("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
        return False

    if not reports:
        logger.info("Telegram notification skipped: No reports to send.")
        return False

    message_html = format_daily_digest(reports)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Telegram daily digest successfully delivered to chat_id {chat}.")
                return True
            else:
                logger.error(f"Telegram API responded with status {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to dispatch Telegram message: {e}")
        return False

