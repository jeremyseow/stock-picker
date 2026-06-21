## 1. Project Initialization

- [x] 1.1 Bootstrap backend Python project (e.g., FastAPI) using `uv` for dependency management, with Pydantic AI and FastMCP.
- [x] 1.2 Bootstrap frontend Next.js project with styling framework (e.g. Tailwind CSS).
- [x] 1.3 Set up a local development database (e.g., PostgreSQL or SQLite) for data persistence.

## 2. Reddit Scraper Service (`reddit-scraper`)

- [x] 2.1 Integrate PRAW to authenticate with the Reddit API in Python.
- [x] 2.2 Create a scheduled job (e.g., APScheduler or Celery) to run at a specific time daily.
- [x] 2.3 Implement logic to fetch exactly the top 20 posts and their top 50 comments from the last 24 hours.
- [x] 2.4 Parse the scraped text to extract tickers, scoring them by weighted engagement.
- [x] 2.5 Isolate the top 5 tickers and bundle the specific comments/posts mentioning them.

## 3. Market Researcher Service (`market-researcher`)

- [x] 3.1 Implement financial API integration to fetch basic market metrics for the top 5 tickers.
- [x] 3.2 Implement news API integration to fetch recent headlines.
- [x] 3.3 Set up Pydantic AI schemas for strict structured JSON output (Report and Buy/Hold/Sell signal).
- [x] 3.4 Write the "Default to HOLD" system prompt and integrate it with the LLM call, passing the bundled Reddit comments for summarization.
- [x] 3.5 Set up an LLM Evaluation framework (e.g., Promptfoo, LangSmith, or custom pytest evals) to test prompt consistency and accuracy.
- [x] 3.6 Persist the generated reports and metrics to the database.

## 4. Dashboard Frontend (`dashboard-frontend`)

- [x] 4.1 Implement FastAPI routes to serve daily top stocks and their detailed reports.
- [x] 4.2 Build the dashboard home page in Next.js to display the daily top tickers.
- [x] 4.3 Build a detailed stock view component showing the report, Reddit summary, and Buy/Sell signal.
- [x] 4.4 Build a statistics component/page to display historical ticker mention trends.

## 5. Integration and Polish

- [x] 5.1 End-to-end test the full pipeline manually.
- [x] 5.2 Add error handling for API rate limits and unexpected LLM outputs.
- [x] 5.3 Polish frontend styling to ensure a responsive, clean user experience.

## 6. Refactor: Direct JSON Scraping

- [x] 6.1 Remove `praw` dependency and install `httpx` and `tenacity`.
- [x] 6.2 Rewrite `reddit_scraper.py` to fetch `/r/wallstreetbets/top.json` using `httpx`.
- [x] 6.3 Implement a polite delay loop to fetch the comments `.json` for the top 20 posts without hitting rate limits.
- [x] 6.4 Update the `run_pipeline.py` script to test the new HTTP-based scraping logic.

## 7. Scraper Fallback & Ticker Validation

- [x] 7.1 Implement `old.reddit.com` HTML fallback scraper when JSON requests get 403-blocked.
- [x] 7.2 Implement `is_valid_ticker` helper in `market_researcher.py` using `yfinance` to check price and market cap.
- [x] 7.3 Update `run_pipeline.py` to sequentially validate candidate tickers and limit to exactly 5 valid stock securities.

## 8. SEC Filings & Web Search Integration

- [x] 8.1 Fetch recent SEC filings list (last 5 entries) for each ticker using `yfinance`.
- [x] 8.2 Integrate DuckDuckGo web search via `ddgs` to gather latest industry news and product launches.
- [x] 8.3 Inject SEC filings and search news into the Gemini prompt to guide the reconciliation analysis.

## 9. Events & Happenings Section

- [x] 9.1 Add `events_happenings` text field to `StockReport` Pydantic schema and system prompt.
- [x] 9.2 Add `events_happenings` column to `TickerReport` SQLAlchemy model and save it in CRUD logic.
- [x] 9.3 Update database CLI queries and plain text endpoints to retrieve and format events.

## 10. Rich Frontend Dashboard Redesign

- [x] 10.1 Enrich `/api/tickers/today` endpoint to return latest report previews (price, recommendation, sector).
- [x] 10.2 Update homepage cards to show recommendation badges, live price, target price, and sector details.
- [x] 10.3 Redesign report detail view with potential upside calculation, a 4-pillar analysis grid, key ratios tables, and clickable news links.
