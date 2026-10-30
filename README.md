# Antigravity StockPicker (Subreddit Stock Analyzer)

An automated market intelligence system that extracts trending stock discussions from Reddit (`r/wallstreetbets`), validates tradeable securities via `yfinance`, gathers financial metrics, SEC filings, and latest news, and performs conservative AI-driven equity evaluations using Gemini. Persisted reports and multi-run historical analytics are served via a FastAPI backend and displayed through a responsive Next.js dashboard.

---

## Architecture Diagram

```mermaid
graph TD
    subgraph Data Ingestion
        A[Reddit RSS Feeds<br/>r/wallstreetbets top & comments] --> C[Scraper & Ticker Extractor<br/>reddit_scraper.py + ticker_extractor.py]
        B1[yfinance API<br/>Metrics & SEC Filings] --> D[Market Researcher<br/>market_researcher.py]
        B2[DuckDuckGo Search<br/>Corporate News & Tech Launches] --> D
    end

    subgraph Pipeline & LLM Synthesis
        SCH[APScheduler<br/>Daily 19:00 SGT] --> RUN[Pipeline Runner<br/>pipeline.py]
        RUN --> C
        C -->|Top 5 Validated Stocks| D
        D -->|Enriched Financial Context| AGENT[Pydantic AI Agent<br/>Gemini 2.5 Pro]
        AGENT -->|Structured StockReport| DB[(SQLite Database<br/>stock_analyzer.db)]
    end

    subgraph Backend API (FastAPI)
        DB --> API[FastAPI Server<br/>main.py]
        API -->|On-Demand Meta-Analysis| TRAJ[Trajectory Meta-Agent<br/>Gemini 2.5 Pro]
        TRAJ --> DB
    end

    subgraph Frontend Dashboard (Next.js 15)
        API --> DASH[Daily Dashboard<br/>/]
        API --> REP[Detailed Intel Report<br/>/report/:ticker]
        API --> HIST[Historical Reports by Date<br/>/stats]
        API --> ANALYTICS[Ticker Analytics & Trajectory<br/>/analytics]
    end
```

---

## Project Structure

```
stock-picker/
├── backend/
│   ├── app/
│   │   ├── agent.py              # Pydantic AI agent for daily reports & trajectory meta-analyses
│   │   ├── crud.py               # Async SQLAlchemy CRUD operations
│   │   ├── database.py           # Engine & async SQLite session management
│   │   ├── llm_schemas.py        # Pydantic schemas (StockReport, TrajectoryAnalysis)
│   │   ├── main.py               # FastAPI endpoints & CORS configuration
│   │   ├── market_researcher.py  # yfinance & DuckDuckGo metrics and news fetcher
│   │   ├── models.py             # SQLAlchemy models (DailyTicker, TickerReport, TickerTrajectoryAnalysis)
│   │   ├── pipeline.py           # Core ingestion, analysis, and persistence pipeline
│   │   ├── reddit_scraper.py     # Atom/RSS feed parser with rate-limit handling
│   │   ├── scheduler.py          # APScheduler cron job (19:00 SGT)
│   │   └── ticker_extractor.py   # Regex extraction and engagement scoring
│   ├── tests/
│   │   ├── test_analytics_api.py # Async integration tests for dates & analytics endpoints
│   │   └── test_evals.py         # LLM evaluation and ticker validation tests
│   ├── pyproject.toml            # Backend dependencies (managed via uv)
│   ├── run_pipeline.py           # CLI script to execute the pipeline manually
│   └── query_report.py           # CLI tool to inspect a report from the database
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Homepage: Daily top stocks from latest run
│   │   │   ├── stats/page.tsx    # Historical Reports explorer with date selector
│   │   │   ├── analytics/page.tsx# Multi-run Ticker Analytics & trajectory chart
│   │   │   └── report/[ticker]/  # Detailed Four-Pillar Intelligence Report view
│   │   └── components/
│   │       ├── Navbar.tsx        # Persistent top navigation bar
│   │       ├── PriceTrajectoryChart.tsx # SVG chart of Market Price vs Target Price
│   │       ├── MetaAnalysisCard.tsx     # On-demand AI Trajectory Meta-Analysis
│   │       ├── SentimentTrajectoryTimeline.tsx # Recommendation & sentiment history
│   │       ├── ValuationMetricsPanel.tsx# P/E ratios and 52-week trading range
│   │       └── ActionableInsightsLog.tsx# Chronological catalysts log
│   ├── package.json
│   └── tsconfig.json
└── openspec/                     # OpenSpec change management and specifications
```

---

## Design Choices & Trade-offs

1. **RSS Feed Ingestion**:
   - *Choice*: Scrapes Reddit Atom/RSS feeds instead of JSON APIs or `old.reddit.com`.
   - *Trade-off*: Works without Reddit API credentials, but RSS omits raw comment counts/scores and is rate-limited (~1 request/60s unauthenticated).
2. **Strict "Default to HOLD" Evaluation Policy**:
   - *Choice*: Pydantic AI prompts instruct Gemini to default to a conservative "HOLD" recommendation unless unambiguous, corroborating evidence supports BUY or SELL.
   - *Trade-off*: Filters out retail meme hype and flags speculative risk, while reducing the frequency of aggressive BUY signals.
3. **On-Demand AI Trajectory Meta-Analysis with SQLite Caching**:
   - *Choice*: Multi-day trajectory meta-analysis is generated on-demand when a user requests it and cached in SQLite keyed by `(ticker, latest_report_id)`.
   - *Trade-off*: Fast initial page loads, zero wasted token costs on repeated visits, and on-demand synthesis when $>1$ run exists.
4. **Zero-Dependency Responsive SVG Charting**:
   - *Choice*: Time-series charts are drawn using pure SVG and Tailwind CSS within React.
   - *Trade-off*: Zero external charting dependencies, no React 19 / Next.js 15 bundle conflicts, and native dark-theme styling.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.11+ and `uv`
- Node.js 18+ and `npm`
- Gemini API Key

### 2. Backend Setup
1. Navigate to `backend`:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Configure `.env`:
   ```ini
   REDDIT_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) HermesAgent/1.1 (Autonomous Research Project)"
   GEMINI_API_KEY=your_gemini_api_key
   ```
4. Start the FastAPI server (starts scheduler at 19:00 SGT):
   ```bash
   uv run uvicorn app.main:app --reload
   ```
   API Swagger docs available at `http://localhost:8000/docs`.

### 3. Frontend Setup
1. Navigate to `frontend`:
   ```bash
   cd frontend
   npm install
   ```
2. Start development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:3000`.

---

## Running Tests

### Backend Unit & Integration Tests:
```bash
cd backend
uv run python -m pytest tests/
```

### Frontend Production Build Test:
```bash
cd frontend
npm run build
```

