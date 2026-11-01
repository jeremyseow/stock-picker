# Antigravity StockPicker (Subreddit Stock Analyzer)

An automated market intelligence system that extracts trending stock discussions from multiple subreddits (`r/wallstreetbets`, `r/stocks`, `r/ValueInvesting`) via official Reddit OAuth, validates tradeable securities via `yfinance`, gathers financial metrics, SEC filings, and latest news, and performs conservative AI-driven equity evaluations using Gemini. Persisted reports and multi-run historical analytics are served via a FastAPI backend and displayed through a responsive Next.js dashboard.

---

## Architecture Diagram

```mermaid
graph TD
    subgraph Data Ingestion
        A[Reddit OAuth API<br/>Multi-sub: WSB, stocks, ValueInvesting] --> C[Engine 1: Retail Momentum<br/>reddit_scraper.py + ticker_extractor.py]
        B1[SEC Form 4 Code P & Congressional PTRs<br/>OpenInsider & Disclosures] --> E2[Engine 2: Smart Money Scout<br/>smart_money_ingestor.py + scorer.py]
        B2[yfinance & DuckDuckGo Search<br/>Financial Metrics & News] --> D[Market Researcher]
    end

    subgraph Pipeline & LLM Synthesis
        C -->|Top 5 Validated Stocks| D
        D --> AGENT[Gemini 4 Argon Agent]
        AGENT --> DB[(SQLite Database<br/>stock_analyzer.db)]
        E2 -->|High Conviction Candidates| RES[Smart Money Researcher]
        RES --> DB
        SYN[Synthesis Hub<br/>synthesis_engine.py] -->|Archetype Classification| DB
    end

    subgraph Backend API (FastAPI)
        DB --> API[FastAPI Server<br/>main.py]
    end

    subgraph Frontend Dashboard (Next.js)
        API --> DASH[Retail Momentum Dashboard<br/>/]
        API --> REP[Retail Intel Report<br/>/report/:ticker]
        API --> SM[Smart Money & Gov Feed<br/>/smart-money]
        API --> SM_REP[Smart Money Catalyst Report<br/>/smart-money/:ticker]
        API --> SYN_PAGE[Cross-Engine Synthesis Matrix<br/>/synthesis]
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
│   │   ├── agent.py                 # Pydantic AI agent for daily reports & trajectory meta-analyses
│   │   ├── crud.py                  # Async SQLAlchemy CRUD operations
│   │   ├── database.py              # Engine & async SQLite session management (anchored to backend/stock_analyzer.db)
│   │   ├── llm_schemas.py           # Pydantic schemas (StockReport, TrajectoryAnalysis, SmartMoneyReport)
│   │   ├── main.py                  # FastAPI endpoints & CORS configuration
│   │   ├── market_researcher.py     # yfinance & DuckDuckGo metrics, news fetcher, and ticker validator
│   │   ├── models.py                # SQLAlchemy models (DailyTicker, TickerReport, SmartMoneyTicker, SynthesisRecord)
│   │   ├── pipeline.py              # Engine 1 ingestion, evaluation, and persistence pipeline
│   │   ├── reddit_scraper.py        # Multi-subreddit Reddit OAuth API client (Client Credentials)
│   │   ├── scheduler.py             # APScheduler cron job (19:00 SGT)
│   │   ├── smart_money_ingestor.py  # Market-wide SEC Form 4 (Code P) and Capitol Hill STOCK Act disclosures
│   │   ├── smart_money_pipeline.py  # Engine 2 orchestrator for Smart Money & Political Scout
│   │   ├── smart_money_researcher.py# Gemini-driven government contract & swing catalyst researcher
│   │   ├── smart_money_scorer.py    # Multi-factor conviction scoring & committee alignment matrix
│   │   ├── synthesis_engine.py      # Cross-Engine matrix correlator (The Rocket, Retail Trap, Silent Accumulation)
│   │   ├── telegram_notifier.py     # Telegram Bot API client with deduplication cache
│   │   └── ticker_extractor.py      # Regex extraction, noise filtering, and engagement scoring
│   ├── scripts/
│   │   └── reset_and_run.py         # Full database wipe & end-to-end multi-engine execution
│   ├── tests/
│   │   ├── test_analytics_api.py    # Async integration tests for dates & analytics endpoints
│   │   ├── test_evals.py            # LLM evaluation and ticker validation tests
│   │   ├── test_smart_money.py      # Form 4 extraction, smart money serialization & guardrails
│   │   ├── test_smart_money_political.py # Engine 2 scoring, committee mapping & archetype tests
│   │   └── test_telegram_notifier.py# Telegram digest formatting & dispatch tests
│   ├── pyproject.toml               # Backend dependencies (managed via uv)
│   ├── run_pipeline.py              # CLI script to execute full pipeline (Engine 1 + Engine 2 + Synthesis)
│   ├── send_test_telegram.py        # CLI tool to test or manually dispatch today's digest
│   └── query_report.py              # CLI tool to inspect a report from the database
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Homepage: Retail Momentum top stocks
│   │   │   ├── smart-money/         # Smart Money & Gov: Market-wide radar & catalyst reports
│   │   │   │   ├── page.tsx         # Inflow Feed & ranked candidates
│   │   │   │   └── [ticker]/page.tsx# Executive inflow ledger & catalyst horizon
│   │   │   ├── synthesis/page.tsx   # Cross-Engine Synthesis Matrix & Retail Awareness Gauge
│   │   │   ├── stats/page.tsx       # Historical Reports explorer with date selector
│   │   │   ├── analytics/page.tsx   # Multi-run Ticker Analytics & trajectory chart
│   │   │   └── report/[ticker]/     # Four-Pillar Report & Smart Money Radar view
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Persistent top navigation bar across all 5 sections
│   │   │   ├── SmartMoneyRadar.tsx  # Form 4 executive flow & Capitol Hill disclosures
│   │   │   ├── PriceTrajectoryChart.tsx # SVG chart of Market Price vs Target Price
│   │   │   ├── MetaAnalysisCard.tsx # On-demand AI Trajectory Meta-Analysis
│   │   │   └── ValuationMetricsPanel.tsx # P/E ratios and 52-week trading range
│   │   └── lib/
│   │       └── api.ts               # Centralized frontend API base URL helper
│   ├── package.json
│   └── tsconfig.json
└── openspec/                        # OpenSpec specifications and archived changes
```

---

## Design Choices & Trade-offs

1. **Multi-Subreddit OAuth API Ingestion**:
   - *Choice*: Scrapes official Reddit OAuth API endpoints (`r/wallstreetbets`, `r/stocks`, `r/ValueInvesting`) using script credentials.
   - *Trade-off*: Requires Reddit client ID/secret, but delivers reliable rate limits (100 req/min), post scores, and comment counts with zero HTML fragility.
2. **Strict "Default to HOLD" Evaluation Policy**:
   - *Choice*: Pydantic AI prompts instruct Gemini to default to a conservative "HOLD" recommendation unless unambiguous, corroborating evidence supports BUY or SELL.
   - *Trade-off*: Filters out retail meme hype and flags speculative risk, while reducing the frequency of aggressive BUY signals.
3. **Dual-Engine Top-Down & Bottom-Up Discovery**:
   - *Choice*: Engine 1 handles bottom-up retail momentum while Engine 2 tracks top-down market-wide insider cluster buying (SEC Form 4 Code P) and Congressional STOCK Act disclosures.
   - *Trade-off*: Independent discovery pipelines prevent retail chatter from biasing institutional signal collection, while Synthesis Matrix uncovers market divergences (The Rocket, Retail Trap, Silent Accumulation).
4. **On-Demand AI Trajectory Meta-Analysis with SQLite Caching**:
   - *Choice*: Multi-day trajectory meta-analysis is generated on-demand when a user requests it and cached in SQLite keyed by `(ticker, latest_report_id)`.
   - *Trade-off*: Fast initial page loads, zero wasted token costs on repeated visits, and on-demand synthesis when $>1$ run exists.
5. **Zero-Dependency Responsive SVG Charting**:
   - *Choice*: Time-series charts are drawn using pure SVG and Tailwind CSS within React.
   - *Trade-off*: Zero external charting dependencies, no React 19 / Next.js 15 bundle conflicts, and native dark-theme styling.
6. **Zero-Cost Smart Money & Insider Radar**:
   - *Choice*: Leverages OpenInsider scraping, native `yfinance` Form 4 transactions, and targeted DuckDuckGo political disclosure queries.
   - *Trade-off*: Eliminates expensive commercial insider data subscriptions (Bloomberg, Quiver Quant), while enforcing hard LLM guardrails (prohibits "BUY" ratings if C-suite executives are liquidating into retail hype).
7. **Automated Telegram Consolidated Digest with Deduplication**:
   - *Choice*: Outbound direct REST calls via `httpx` to Telegram Bot API with hash-based deduplication cache and HTML parse mode.
   - *Trade-off*: Guarantees zero duplicate alerts across rapid invocations while skipping dispatch gracefully when unconfigured.

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
   # Reddit OAuth API Credentials (required)
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT="python:stock-picker:v1.0.0 (by /u/stock-picker-bot)"
   # Optional: Subreddits to scrape (comma-separated, default: wallstreetbets,stocks,ValueInvesting)
   REDDIT_SUBREDDITS="wallstreetbets,stocks,ValueInvesting"

   GEMINI_API_KEY=your_gemini_api_key

   # Optional: Telegram Daily Digest Alerts (leave blank to disable)
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   TELEGRAM_CHAT_ID=your_chat_or_channel_id
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

