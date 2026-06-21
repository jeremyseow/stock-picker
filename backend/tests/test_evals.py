import pytest
import os
from app.agent import generate_stock_report
from app.llm_schemas import StockReport

# To run this correctly, you'd need a real LLM API key, but we can set up the scaffolding.

@pytest.mark.asyncio
async def test_eval_default_to_hold_on_mixed_signals():
    """
    Eval: Ensure the LLM correctly defaults to HOLD when signals are mixed.
    """
    # Mock mixed data
    market_metrics = {"pe_ratio": 150, "price": 10} # high PE is bad
    recent_news = ["Company announces new product, but faces lawsuit."]
    sec_filings = "- 2026-06-01 (10-Q): Revenue flat, increasing legal expenses."
    web_search_news = "- Lawsuit filing details (URL: ...)\n  Snippet: Competitor sues company for patent infringement."
    reddit_context = "[COMMENT | Score: 50]: This stock is going to the moon!\\n[COMMENT | Score: 10]: They are burning cash too fast."
    
    # We skip actual API call in CI if no key
    if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "mock_key":
        report = await generate_stock_report("MOCK", market_metrics, recent_news, reddit_context, sec_filings, web_search_news)
        assert report.recommendation == "HOLD", "Model should default to HOLD on mixed signals."

@pytest.mark.asyncio
async def test_eval_buy_on_overwhelming_positive():
    """
    Eval: Ensure the LLM issues a BUY only on overwhelmingly positive data.
    """
    market_metrics = {"pe_ratio": 15, "price": 100, "forward_pe": 10, "industry": "Tech"} 
    recent_news = ["Company crushes earnings, raises guidance significantly.", "New AI chip is a massive success."]
    sec_filings = "- 2026-06-01 (10-Q): Revenue up 50% YoY, data center scaling accelerated."
    web_search_news = "- Company launches revolutionary AI chip to massive acclaim (URL: ...)\n  Snippet: Industry experts confirm chip outperforms all rivals."
    reddit_context = "[POST | Score: 5000]: $MOCK just won the AI war. Buying 1000 shares.\\n[COMMENT | Score: 2000]: This is the most obvious buy of the decade."
    
    if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "mock_key":
        report = await generate_stock_report("MOCK", market_metrics, recent_news, reddit_context, sec_filings, web_search_news)
        assert report.recommendation == "BUY", "Model should BUY on overwhelmingly positive signals."

def test_is_valid_ticker():
    """
    Test ticker validation against known tickers and common noise words.
    """
    from app.market_researcher import is_valid_ticker
    assert is_valid_ticker("MSFT") is True
    assert is_valid_ticker("AAPL") is True
    assert is_valid_ticker("OP") is False
    assert is_valid_ticker("CALLS") is False

