import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from app.market_researcher import is_valid_ticker, fetch_insider_data

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


CAPITOLTRADES_TRADES_URL = "https://www.capitoltrades.com/trades?page={page}"
CAPITOLTRADES_BUY_URL = CAPITOLTRADES_TRADES_URL


def _normalize_capitol_amount(raw_amt: str) -> str:
    """Normalizes CapitolTrades shorthand ranges (e.g. '15K–50K') into STOCK Act brackets."""
    clean = re.sub(r"[^\w]", "", (raw_amt or "").upper())
    mapping = {
        "1K15K": "$1,001 - $15,000",
        "15K50K": "$15,001 - $50,000",
        "50K100K": "$50,001 - $100,000",
        "100K250K": "$100,001 - $250,000",
        "250K500K": "$250,001 - $500,000",
        "500K1M": "$500,001 - $1,000,000",
        "1M5M": "$1,000,001 - $5,000,000",
        "5M25M": "$5,000,001 - $25,000,000",
        "25M50M": "$25,000,001 - $50,000,000",
    }
    if clean in mapping:
        return mapping[clean]
    if raw_amt:
        return re.sub(r"[\u2013\u2014\ufffd]+", " - ", raw_amt.strip())
    return "$15,001 - $50,000"


def _parse_capitol_date(raw_date: str) -> str:
    """Parses CapitolTrades date strings ('14:01 | Today', '20 Oct | 2026') to YYYY-MM-DD."""
    text = (raw_date or "").strip()
    if "Today" in text:
        return datetime.now().strftime("%Y-%m-%d")
    if "Yesterday" in text:
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    cleaned = re.sub(r"\s*\|\s*", " ", text).strip()
    m = re.search(r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", cleaned)
    if m:
        try:
            return datetime.strptime(m.group(1), "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d")


async def _fetch_capitol_politician_committees(client: httpx.AsyncClient, pol_href: str, headers: dict) -> Optional[str]:
    """Fetches official Congressional committees from the lawmaker's CapitolTrades profile."""
    if not pol_href or not pol_href.startswith("/politicians/"):
        return None
    try:
        url = f"https://www.capitoltrades.com{pol_href}"
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for span in soup.find_all("span"):
                if span.get_text(strip=True) == "Committees":
                    parent = span.parent
                    items = [li.get_text(strip=True) for li in parent.find_all("li") if li.get_text(strip=True)]
                    if items:
                        return ", ".join(items)
    except Exception as e:
        logger.debug(f"Failed to fetch committees for {pol_href}: {e}")
    return None


async def _fetch_capitoltrades_html(limit: int = 25, max_pages: int = 3) -> List[Dict[str, Any]]:
    """Scrapes live STOCK Act purchase filings directly from CapitolTrades SSR HTML."""
    trades: List[Dict[str, Any]] = []
    seen = set()
    valid_cache: Dict[str, bool] = {}
    committee_cache: Dict[str, Optional[str]] = {}
    headers = {"User-Agent": DEFAULT_USER_AGENT}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            if len(trades) >= limit:
                break
            url = CAPITOLTRADES_BUY_URL.format(page=page)
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                logger.warning(f"CapitolTrades returned HTTP {res.status_code} on page {page}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table tbody tr")
            if not rows:
                break

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 10:
                    continue

                # Col 0: Politician | Party | Chamber | State
                pol_parts = [p.strip() for p in cols[0].get_text(" | ", strip=True).split("|")]
                politician = pol_parts[0] if pol_parts else "Congressional Member"
                party = pol_parts[1] if len(pol_parts) > 1 else None
                chamber = pol_parts[2] if len(pol_parts) > 2 else None

                # Extract committee assignments from lawmaker profile if linked
                pol_a = cols[0].find("a")
                pol_href = pol_a.get("href") if pol_a else None
                committee = None
                if pol_href and pol_href.startswith("/politicians/"):
                    if pol_href not in committee_cache:
                        committee_cache[pol_href] = await _fetch_capitol_politician_committees(client, pol_href, headers)
                    committee = committee_cache.get(pol_href)

                # Col 1: Issuer Name | TICKER:US
                issuer_parts = [p.strip() for p in cols[1].get_text(" | ", strip=True).split("|")]
                company = issuer_parts[0] if issuer_parts else ""
                raw_sym = issuer_parts[1] if len(issuer_parts) > 1 else ""
                if not raw_sym.endswith(":US"):
                    continue
                ticker = raw_sym.split(":")[0].upper().strip()
                if not ticker or not re.match(r"^[A-Z]{1,5}$", ticker):
                    continue
                if ticker in ["USD", "ETF", "SPY", "QQQ"]:
                    continue

                tx_type = cols[6].get_text(strip=True).upper()
                if tx_type not in ["BUY", "SELL"]:
                    continue

                if ticker not in valid_cache:
                    valid_cache[ticker] = is_valid_ticker(ticker)
                if not valid_cache[ticker]:
                    continue

                filing_date = _parse_capitol_date(cols[2].get_text(" | ", strip=True))
                trade_date = _parse_capitol_date(cols[3].get_text(" | ", strip=True))
                amount_range = _normalize_capitol_amount(cols[7].get_text(strip=True))
                price_txt = cols[8].get_text(strip=True)

                detail_link = cols[9].find("a")
                href = detail_link.get("href") if detail_link else ""
                source_url = f"https://www.capitoltrades.com{href}" if href and href.startswith("/") else "https://www.capitoltrades.com/trades"

                dedup_key = (ticker, politician, trade_date, tx_type)
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                meta_desc = ", ".join(x for x in [party, chamber] if x)
                pol_label = f"{politician} ({meta_desc})" if meta_desc else politician
                action_desc = "purchase" if tx_type == "BUY" else "sale"
                snippet = f"{pol_label} disclosed {action_desc} of {amount_range} in {company} ({ticker}) traded {trade_date}, filed {filing_date}."

                trades.append({
                    "ticker": ticker,
                    "politician": politician,
                    "party": party,
                    "chamber": chamber,
                    "committee": committee,
                    "transaction_type": tx_type,
                    "amount_range": amount_range,
                    "price": price_txt if price_txt and price_txt != "N/A" else None,
                    "trade_date": trade_date,
                    "filing_date": filing_date,
                    "source_url": source_url,
                    "snippet": snippet,
                })
                if len(trades) >= limit:
                    break

    return trades


async def fetch_recent_congressional_purchases(limit: int = 25) -> List[Dict[str, Any]]:
    """
    Discovers recent Congressional STOCK Act purchases across House and Senate members.
    Uses live CapitolTrades SSR filings table as primary authoritative source.
    """
    trades: List[Dict[str, Any]] = []

    # Primary: Live CapitolTrades HTML table
    try:
        trades = await _fetch_capitoltrades_html(limit=limit)
        if trades:
            logger.info(f"Ingested {len(trades)} live Congressional STOCK Act trades from CapitolTrades.")
            return trades
    except Exception as e:
        logger.error(f"CapitolTrades live scrape failed: {e}")

    # Fallback: strict lawmaker regex search, explicitly rejecting aggregator tracker names
    queries = [
        "site:capitoltrades.com/trades purchase disclosure 2026",
    ]
    seen_fallback = set()

    try:
        ddgs = DDGS()
        for q in queries:
            try:
                results = list(ddgs.text(q, max_results=10))
                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    text = f"{title} {body}"

                    politician_match = re.search(r"(Rep\.|Senator|Sen\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
                    if not politician_match:
                        continue
                    pol_name = politician_match.group(0)
                    if any(t in pol_name.lower() for t in ["tracker", "feed", "aggregate", "quant"]):
                        continue

                    ticker_matches = re.findall(
                        r"\$([A-Z]{1,5})\b|\(([A-Z]{1,5}):US\)|\(([A-Z]{1,5})\)|\b([A-Z]{2,5})\s+stock\b",
                        text,
                    )
                    found_tickers = [next((g for g in m if g), None) for m in ticker_matches]
                    found_tickers = [t for t in found_tickers if t]

                    for t in found_tickers:
                        t = t.upper()
                        if t in ["USD", "ETF", "SPY", "QQQ", "US"]:
                            continue
                        if is_valid_ticker(t):
                            amount_match = re.search(r"(\$\d+k?\s*[-–]\s*\$?\d+k?|\$\d+[\d,]+)", text, re.I)
                            amount_str = amount_match.group(1) if amount_match else "$15,001 - $50,000"

                            dedup_key = (t, pol_name, title[:40])
                            if dedup_key in seen_fallback:
                                continue
                            seen_fallback.add(dedup_key)

                            tx_type = "SELL" if any(w in text.lower() for w in ["sold", "sale", "dumped"]) else "BUY"
                            trades.append({
                                "ticker": t,
                                "politician": pol_name,
                                "party": None,
                                "chamber": "Senate" if "sen" in pol_name.lower() else "House",
                                "committee": None,
                                "transaction_type": tx_type,
                                "amount_range": amount_str,
                                "source_url": href or title,
                                "snippet": body[:200],
                                "trade_date": datetime.now().strftime("%Y-%m-%d"),
                            })
                            if len(trades) >= limit:
                                break
                    if len(trades) >= limit:
                        break
            except Exception as e:
                logger.warning(f"Congressional query '{q}' encountered: {e}")

        logger.info(f"Ingested {len(trades)} candidate Congressional trades via fallback.")
    except Exception as e:
        logger.error(f"Error fetching Congressional purchases: {e}")

    return trades


def fetch_form4_flows_for_tickers(tickers: List[str], limit_per_ticker: int = 8) -> List[Dict[str, Any]]:
    """
    Engine 2 Form 4 ingestion for both purchases and executive liquidations (SELLs)
    across monitored tickers (including Engine 1 hyped stocks for Retail Trap detection).
    """
    rows: List[Dict[str, Any]] = []
    seen = set()
    for sym in tickers:
        clean_sym = (sym or "").strip().upper()
        if not clean_sym or clean_sym in seen:
            continue
        seen.add(clean_sym)
        try:
            ins_data = fetch_insider_data(clean_sym, limit=limit_per_ticker)
            if not ins_data or not ins_data.get("has_data"):
                continue
            for tx in ins_data.get("recent_transactions", []):
                tx_type = str(tx.get("type") or "OTHER").upper()
                rows.append({
                    "ticker": clean_sym,
                    "filing_date": tx.get("date") or "",
                    "trade_date": tx.get("date") or "",
                    "insider_name": tx.get("insider") or "Executive",
                    "position": tx.get("position") or "Insider",
                    "transaction_type": tx_type,
                    "shares": float(tx.get("shares") or 0.0),
                    "price": str(tx.get("price") or ""),
                    "total_value": float(tx.get("value") or 0.0),
                    "ownership": str(tx.get("ownership") or ""),
                    "filing_details": tx.get("details") or tx.get("text") or "SEC Form 4",
                    "company_name": tx.get("details") or tx.get("text") or "SEC Form 4",
                })
        except Exception as e:
            logger.warning(f"Failed Form 4 flow fetch for ${clean_sym}: {e}")
    return rows


async def ingest_all_smart_money() -> Dict[str, Any]:
    """Ingests both Form 4 purchases and Congressional disclosures."""
    insider_trades = await fetch_recent_insider_purchases(limit=50)
    congress_trades = await fetch_recent_congressional_purchases(limit=20)
    return {
        "insider_trades": insider_trades,
        "congress_trades": congress_trades,
    }

