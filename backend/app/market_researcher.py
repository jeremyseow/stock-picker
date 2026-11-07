import yfinance as yf
import logging
import re
from ddgs import DDGS
from app.ticker_extractor import TICKER_ALIASES

logger = logging.getLogger(__name__)

def fetch_financial_metrics(ticker_symbol: str) -> dict:
    """
    Fetches basic market metrics for a given ticker using yfinance.
    """
    ticker_symbol = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    logger.info(f"Fetching financial metrics for {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Extract key metrics
        metrics = {
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "target_price": info.get("targetMeanPrice"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "industry": info.get("industry", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "recommendation_key": info.get("recommendationKey", "none")
        }
        return metrics
    except Exception as e:
        logger.error(f"Error fetching data for {ticker_symbol}: {e}")
        return {"error": str(e)}

def fetch_sec_filings(ticker_symbol: str, limit: int = 5) -> list:
    """
    Fetches recent SEC filings list for a given ticker using yfinance.
    """
    logger.info(f"Fetching SEC filings for {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        filings = stock.sec_filings
        if not filings:
            return []
            
        formatted_filings = []
        for item in filings[:limit]:
            date_str = str(item.get("date", ""))
            formatted_filings.append({
                "date": date_str,
                "type": item.get("type", "Unknown"),
                "title": item.get("title", ""),
                "edgarUrl": item.get("edgarUrl", "")
            })
        return formatted_filings
    except Exception as e:
        logger.error(f"Error fetching SEC filings for {ticker_symbol}: {e}")
        return []

def fetch_recent_news(ticker_symbol: str, limit: int = 5) -> list:
    """
    Fetches recent news headlines for a given ticker using yfinance with DDGS news fallback.
    """
    ticker_clean = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    logger.info(f"Fetching recent news for {ticker_clean}")

    # Attempt 1: yfinance stock.news
    try:
        stock = yf.Ticker(ticker_clean)
        news_items = stock.news
        if news_items:
            headlines = []
            for item in news_items[:limit]:
                headlines.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "link": item.get("link"),
                    "provider_publish_time": item.get("providerPublishTime")
                })
            if headlines:
                return headlines
    except Exception as e:
        logger.warning(f"yfinance news unavailable for {ticker_clean} ({e}), falling back to DDGS news.")

    # Attempt 2: DuckDuckGo dedicated news search
    try:
        with DDGS() as ddgs:
            results = ddgs.news(f"{ticker_clean} stock", max_results=limit)
            headlines = []
            for r in results:
                headlines.append({
                    "title": r.get("title"),
                    "publisher": r.get("source") or "Corporate Press",
                    "link": r.get("url"),
                    "provider_publish_time": None
                })
            if headlines:
                return headlines
    except Exception as e:
        logger.warning(f"DDGS news search failed for {ticker_clean}: {e}")

    # Attempt 3: General DDGS web search fallback
    try:
        web_results = fetch_web_search_news(ticker_clean, limit=limit)
        if web_results:
            return [
                {
                    "title": w.get("title"),
                    "publisher": "Web Search",
                    "link": w.get("link"),
                    "provider_publish_time": None
                }
                for w in web_results
            ]
    except Exception:
        pass

    return []

def fetch_web_search_news(ticker_symbol: str, limit: int = 3) -> list:
    """
    Performs a web search to fetch the latest stock and industry news (tech advancements, launches, etc.).
    """
    ticker_symbol = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    query = f"{ticker_symbol} stock latest news product launch tech advancement"
    logger.info(f"Running web search for {ticker_symbol} with query: '{query}'")
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=limit)
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })
            return formatted
    except Exception as e:
        logger.error(f"Error executing web search for {ticker_symbol}: {e}")
        return []

def fetch_insider_data(ticker_symbol: str, limit: int = 8) -> dict:
    """
    Fetches aggregate 6-month insider purchase/sales and recent Form 4 transactions using yfinance.
    """
    ticker_symbol = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    logger.info(f"Fetching insider data for {ticker_symbol}")
    default_payload = {
        "has_data": False,
        "purchases_shares": 0.0,
        "purchases_trans": 0,
        "sales_shares": 0.0,
        "sales_trans": 0,
        "net_shares": 0.0,
        "total_held": 0.0,
        "sentiment_label": "Neutral / No Data",
        "recent_transactions": []
    }
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # 1. Parse aggregate 6-month purchases/sales
        purchases_df = stock.insider_purchases
        purchases_shares = 0.0
        purchases_trans = 0
        sales_shares = 0.0
        sales_trans = 0
        net_shares = 0.0
        total_held = 0.0

        if purchases_df is not None and not purchases_df.empty:
            records = purchases_df.to_dict(orient="records")
            for row in records:
                label = str(row.get("Insider Purchases Last 6m", "")).strip()
                shares_val = float(row.get("Shares") or 0.0) if row.get("Shares") is not None else 0.0
                trans_val = int(row.get("Trans") or 0) if row.get("Trans") is not None and not str(row.get("Trans")).lower() in ["nan", "none", "<na>"] else 0
                
                if label == "Purchases":
                    purchases_shares = shares_val
                    purchases_trans = trans_val
                elif label == "Sales":
                    sales_shares = shares_val
                    sales_trans = trans_val
                elif "Net Shares" in label:
                    net_shares = shares_val
                elif "Total Insider Shares" in label:
                    total_held = shares_val

        # 2. Parse recent Form 4 transactions
        transactions_df = stock.insider_transactions
        formatted_tx = []
        if transactions_df is not None and not transactions_df.empty:
            tx_records = transactions_df.head(limit).to_dict(orient="records")
            for t in tx_records:
                # Handle dates and timestamps safely
                start_date = t.get("Start Date")
                date_str = str(start_date).split()[0] if start_date is not None else "Unknown"
                
                shares = int(t.get("Shares") or 0) if t.get("Shares") is not None else 0
                value = int(t.get("Value") or 0) if t.get("Value") is not None else 0
                text = str(t.get("Text") or "")
                insider_name = str(t.get("Insider") or "Unknown")
                position = str(t.get("Position") or "Insider")
                
                # Determine transaction type
                tx_type = "SELL" if "sale" in text.lower() else ("BUY" if "purchase" in text.lower() else "OTHER")
                
                # Extract execution price if present
                price_match = re.search(r'(?:at price|price:?)\s+([\d]+(?:\.\d+)?(?:\s*-\s*[\d]+(?:\.\d+)?)?)', text, re.I)
                if price_match:
                    raw_p = price_match.group(1).strip()
                    if "-" in raw_p:
                        price_str = " - ".join(f"${p.strip()}" for p in raw_p.split("-"))
                    else:
                        price_str = f"${raw_p}" if not raw_p.startswith("$") else raw_p
                elif value > 0 and shares > 0:
                    price_str = f"${(value / shares):.2f}"
                else:
                    price_str = "-"

                cleaned_details = re.sub(r'at price\s+[\$\d\s.,-]+per share\.?', '', text, flags=re.I)
                cleaned_details = re.sub(r'at price\s+[\$\d\s.,-]+\.?', '', cleaned_details, flags=re.I).strip()
                cleaned_details = re.sub(r'Stock Award\(Grant\)', 'Stock Award (Grant)', cleaned_details, flags=re.I)
                if not cleaned_details:
                    cleaned_details = text

                formatted_tx.append({
                    "date": date_str,
                    "insider": insider_name,
                    "position": position,
                    "shares": shares,
                    "value": value,
                    "price": price_str,
                    "details": cleaned_details,
                    "text": text,
                    "type": tx_type,
                    "ownership": str(t.get("Ownership") or "D")
                })

        has_data = bool(purchases_shares > 0 or sales_shares > 0 or formatted_tx)
        
        # Derive sentiment label
        if not has_data:
            sentiment_label = "No Recent Form 4 Filings"
        elif net_shares < -100_000 or (sales_shares > purchases_shares * 3 and sales_shares > 500_000):
            sentiment_label = "Heavy Net Insider Selling"
        elif net_shares > 50_000 or (purchases_shares > sales_shares and purchases_shares > 100_000):
            sentiment_label = "Net Insider Accumulation"
        elif sales_shares > purchases_shares:
            sentiment_label = "Moderate Insider Selling"
        else:
            sentiment_label = "Neutral / Balanced Activity"

        return {
            "has_data": has_data,
            "purchases_shares": purchases_shares,
            "purchases_trans": purchases_trans,
            "sales_shares": sales_shares,
            "sales_trans": sales_trans,
            "net_shares": net_shares,
            "total_held": total_held,
            "sentiment_label": sentiment_label,
            "recent_transactions": formatted_tx
        }
    except Exception as e:
        logger.error(f"Error fetching insider data for {ticker_symbol}: {e}")
        return default_payload

def fetch_congressional_trades(ticker_symbol: str, limit: int = 3) -> list:
    """
    Searches for recent Congressional and Senate STOCK Act disclosure reports for the given ticker.
    """
    ticker_symbol = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    query = f"{ticker_symbol} stock congressional trading disclosure representative senator purchase sale"
    logger.info(f"Running Congressional trading search for {ticker_symbol} with query: '{query}'")
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=limit)
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                })
            return formatted
    except Exception as e:
        logger.error(f"Error executing congressional web search for {ticker_symbol}: {e}")
        return []

def is_valid_ticker(ticker_symbol: str) -> bool:
    """
    Validates a ticker symbol by checking if yfinance has a valid price, market cap, and active trading.
    This helps filter out noise words like OP, CALLS, SOH, CNBC, PE, JUST, PC.
    """
    ticker_symbol = TICKER_ALIASES.get(ticker_symbol.upper(), ticker_symbol.upper())
    logger.info(f"Validating ticker symbol: {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")
        volume = info.get("averageVolume") or info.get("volume") or info.get("regularMarketVolume") or 0
        quote_type = (info.get("quoteType") or "").upper()

        if price is not None and market_cap is not None and market_cap > 5_000_000 and volume > 0:
            if quote_type in ("", "EQUITY"):
                logger.info(f"Ticker {ticker_symbol} is valid (Price: {price}, Market Cap: {market_cap}, Volume: {volume})")
                return True
    except Exception as e:
        logger.warning(f"Validation error/failed for ticker {ticker_symbol}: {e}")
    logger.info(f"Ticker {ticker_symbol} is INVALID")
    return False

