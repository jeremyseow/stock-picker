import yfinance as yf
import logging
from ddgs import DDGS

logger = logging.getLogger(__name__)

def fetch_financial_metrics(ticker_symbol: str) -> dict:
    """
    Fetches basic market metrics for a given ticker using yfinance.
    """
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
    Fetches recent news headlines for a given ticker using yfinance.
    """
    logger.info(f"Fetching recent news for {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        news_items = stock.news
        
        headlines = []
        for item in news_items[:limit]:
            headlines.append({
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "provider_publish_time": item.get("providerPublishTime")
            })
            
        return headlines
    except Exception as e:
        logger.error(f"Error fetching news for {ticker_symbol}: {e}")
        return []

def fetch_web_search_news(ticker_symbol: str, limit: int = 3) -> list:
    """
    Performs a web search to fetch the latest stock and industry news (tech advancements, launches, etc.).
    """
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

def is_valid_ticker(ticker_symbol: str) -> bool:
    """
    Validates a ticker symbol by checking if yfinance has a valid price and market cap.
    This helps filter out noise words like OP, CALLS, SOH, CNBC, PE, JUST.
    """
    logger.info(f"Validating ticker symbol: {ticker_symbol}")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")
        if price is not None and market_cap is not None:
            logger.info(f"Ticker {ticker_symbol} is valid (Price: {price}, Market Cap: {market_cap})")
            return True
    except Exception as e:
        logger.warning(f"Validation error/failed for ticker {ticker_symbol}: {e}")
    logger.info(f"Ticker {ticker_symbol} is INVALID")
    return False

