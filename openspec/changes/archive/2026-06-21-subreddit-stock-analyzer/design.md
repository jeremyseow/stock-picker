## Context

The system requires an automated pipeline to scrape a specific subreddit for highly discussed stocks, perform market research, generate a daily report, and display it on a frontend dashboard. Currently, there is no existing infrastructure in this project for scheduled scraping, complex third-party API integration for financial data, report generation, or a standalone frontend dashboard.

## Goals / Non-Goals

**Goals:**
- Reliable daily extraction of trending stock tickers from a targeted subreddit.
- Integration with external APIs (e.g., news APIs, financial metrics APIs, SEC filings, web search news, and LLMs) to generate comprehensive reports including industry insights, news, sentiment, key events, and buy/sell signals.
- A responsive, easily accessible frontend dashboard to present the reports and related statistics clearly.
- Establish an evaluation framework to test the accuracy and consistency of LLM Buy/Sell recommendations.
- Filter out non-stock uppercase noise and ETFs to ensure reports are only created for actual tradeable stocks.

**Non-Goals:**
- High-frequency trading or real-time (minute-by-minute) updates. The focus is on a daily digest.
- Creating a custom machine learning model for sentiment analysis from scratch (we will rely on existing APIs/LLMs).

## Decisions

**1. Backend Architecture: Python + Pydantic AI + FastMCP**
- *Decision*: The backend service will be built in Python, managed by `uv` for lightning-fast dependency resolution, leveraging Pydantic AI for structured LLM interactions and FastMCP for tooling/context injection.
- *Rationale*: Python is the industry standard for AI/LLM engineering. `uv` ensures reproducible and fast environment setups. Pydantic AI natively enforces structured outputs (crucial for our strict schemas), and the Python ecosystem offers trailing PE, forward PE, and standard evaluation tooling (pytest) to check prompts.

**2. Scraping Mechanism: Direct JSON with Old Reddit HTML Fallback**
- *Decision*: We will scrape Reddit's public `.json` endpoints directly (e.g., `/r/wallstreetbets/top.json`) using `httpx` with a custom User-Agent. If requests are blocked by a 403 Forbidden error, we will fall back to an HTML scraper parsing listings and comments from `old.reddit.com` using HTML/Regex logic. Deliberate delays (e.g., 1.5s) are added to ensure polite scraping.
- *Rationale*: Guarantees high scraper reliability by bypassing React client challenges and 403 blocks while avoiding any official OAuth client friction.

**3. Ticker Validation Filtering via yfinance**
- *Decision*: Validate all extracted candidates against `yfinance` before generating reports. A symbol is only considered valid if it returns a valid price (`currentPrice` or `regularMarketPrice`) and a valid `marketCap`.
- *Rationale*: Eliminates colloquial uppercase noise (like `OP`, `CNBC`, `CALLS`, `JUST`) and index ETFs (like `SPY`, `QQQ`), ensuring the system only uses token space and compute for actual corporate equities.

**4. SEC Filings & DuckDuckGo Web Search Integration**
- *Decision*: Supplement financial ratios with the company's last 5 SEC filings (from `yfinance`) and a live web search of latest news and product launches (using `ddgs` wrapper).
- *Rationale*: Provides the LLM with ground-truth compliance data and real-time events to reconcile against speculative retail sentiment.

**5. Report Generation, Prompting, and UI Architecture**
- *Decision*: Synthesize Reddit sentiment, SEC filings, and search news into a structured `StockReport` (defaulting to "HOLD" on mixed signals) containing distinct pillars: Sentiment, Ground Truth, Events & Happenings, and Reconciliation Analysis. Expose these through an enriched API and a premium dark-themed Next.js dashboard featuring a 4-pillar layout.

## Risks / Trade-offs

- **Risk: LLM Hallucinations / Inconsistent Advice** → *Mitigation*: We are implementing an LLM Eval framework natively in Python to run regressions on the prompts and ensure "Default to HOLD" works reliably.
- **Risk: Reddit Rate Limits (429 Errors)** → *Mitigation*: Scraping public `.json` endpoints without auth is heavily monitored. We will mitigate this by capping scrapes to Top 20 posts / 50 comments and adding deliberate sleep delays (e.g., 1.5s) between comment extraction requests to ensure polite scraping.
