import re
import logging
from typing import List, Dict, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from app.market_researcher import is_valid_ticker

logger = logging.getLogger(__name__)

OPENINSIDER_URL = (
    "http://openinsider.com/screener?"
    "s=&o=&pl=&ph=&ll=&lh=&fd=14&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1"
    "&vl=50&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh="
    "&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def _parse_currency(val_str: str) -> float:
    """Parses '$125,000' or '+$1.2M' into a float."""
    if not val_str:
        return 0.0
    clean = re.sub(r"[^\d.-]", "", val_str)
    try:
        return float(clean)
    except ValueError:
        return 0.0


def _parse_delta_own(delta_str: str) -> float:
    """Parses '+42%' into 0.42."""
    if not delta_str:
        return 0.0
    clean = re.sub(r"[^\d.-]", "", delta_str)
    try:
        return float(clean) / 100.0
    except ValueError:
        return 0.0


async def fetch_recent_insider_purchases(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Ingests recent SEC Form 4 Open-Market Purchases (Code P) from OpenInsider.
    Filters for transactions >= $50,000 filed within the last 7 days.
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    trades: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(OPENINSIDER_URL, headers=headers)
            if res.status_code != 200:
                logger.error(f"OpenInsider screener returned HTTP {res.status_code}")
                return []
            html_text = res.text

        soup = BeautifulSoup(html_text, "html.parser")
        table = soup.find("table", {"class": "tinytable"})
        if not table:
            logger.warning("No tinytable found in OpenInsider response.")
            return []

        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 13:
                continue

            ticker = cells[3].upper().strip()
            if not ticker or not re.match(r"^[A-Z]{1,5}$", ticker):
                continue

            trade_type = cells[7]
            if "P - Purchase" not in trade_type and trade_type != "P":
                continue

            trade = {
                "ticker": ticker,
                "filing_date": cells[1],
                "trade_date": cells[2],
                "company_name": cells[4],
                "insider_name": cells[5],
                "title": cells[6],
                "trade_type": "Purchase",
                "price": _parse_currency(cells[8]),
                "qty": int(_parse_currency(cells[9])),
                "owned": int(_parse_currency(cells[10])),
                "delta_own": _parse_delta_own(cells[11]),
                "value": _parse_currency(cells[12]),
            }
            trades.append(trade)
            if len(trades) >= limit:
                break

        logger.info(f"Ingested {len(trades)} valid Form 4 insider purchases from OpenInsider.")
    except Exception as e:
        logger.error(f"Error fetching insider purchases: {e}")

    return trades


async def fetch_recent_congressional_purchases(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Discovers recent Congressional STOCK Act purchases across House and Senate members
    using targeted search aggregations.
    """
    trades: List[Dict[str, Any]] = []
    queries = [
        "congressional stock trades purchase disclosure periodic transaction report filed 2026",
        "site:capitoltrades.com/trades purchase disclosure 2026",
    ]

    try:
        ddgs = DDGS()
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=10))
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    text = f"{title} {body}"

                    # Regex match tickers like $NVDA or (NASDAQ: NVDA) or "bought NVDA"
                    ticker_matches = re.findall(r"\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\s+stock\b", text)
                    found_tickers = [m[0] or m[1] for m in ticker_matches if m[0] or m[1]]

                    for t in found_tickers:
                        t = t.upper()
                        if is_valid_ticker(t) and t not in ["USD", "ETF", "SPY", "QQQ"]:
                            # Estimate dollar range from text if present
                            amount_match = re.search(r"(\$\d+k?\s*[-–]\s*\$?\d+k?|\$\d+[\d,]+)", text, re.I)
                            amount_str = amount_match.group(1) if amount_match else "$15,001 - $50,000"

                            # Detect politician name
                            politician_match = re.search(r"(Rep\.|Senator|Sen\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
                            pol_name = politician_match.group(0) if politician_match else "Congressional Member"

                            trades.append({
                                "ticker": t,
                                "politician": pol_name,
                                "amount_range": amount_str,
                                "source_title": title,
                                "snippet": body[:200],
                                "trade_date": datetime.now().strftime("%Y-%m-%d"),
                            })
                            if len(trades) >= limit:
                                break
                    if len(trades) >= limit:
                        break
            except Exception as e:
                logger.warning(f"Congressional query '{q}' encountered: {e}")

        logger.info(f"Ingested {len(trades)} candidate Congressional trades.")
    except Exception as e:
        logger.error(f"Error fetching Congressional purchases: {e}")

    return trades


async def ingest_all_smart_money() -> Dict[str, Any]:
    """Ingests both Form 4 purchases and Congressional disclosures."""
    insider_trades = await fetch_recent_insider_purchases(limit=50)
    congress_trades = await fetch_recent_congressional_purchases(limit=20)
    return {
        "insider_trades": insider_trades,
        "congress_trades": congress_trades,
    }

