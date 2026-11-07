# Antigravity StockPicker (Subreddit Stock Analyzer)

An automated market intelligence system that discovers equity opportunities through three parallel scanning engines:
1. **Engine 1 (Retail Momentum Scout)**: Scrapes trending stock discussions across Reddit (`r/wallstreetbets`, `r/stocks`, `r/ValueInvesting`) via official Reddit OAuth API.
2. **Engine 2 (Smart Money & Political Scout)**: Aggregates SEC Form 4 insider cluster purchases and Capitol Hill STOCK Act disclosures.
3. **Engine 3 (Institutional Whale Options Radar)**: Scrapes equity option chains to detect unusual Volume > $2.5\times$ Open Interest spikes, aggressive out-of-the-money call sweeps, and put/call volume skews.

All discovery engines link into a decoupled, reusable **Core Equity Intelligence Engine (`CoreEquityReport`)** that independently gathers fundamental metrics, SEC 10-Q/8-K disclosures, and DuckDuckGo corporate news, synthesizing objective ground truth and risk profiles with 6-hour caching. Engines 1, 2, and 3 attach specialized overlays (`RetailSentimentReport`, `SmartMoneyReport`, `OptionsWhaleReport`) over the core record, while the **Cross-Engine Synthesis Hub** correlates divergence across engines into a 3-way Triangulation Matrix (`SynthesisReport`) to classify stocks into market archetypes (*The Rocket*, *Silent Accumulation / Stealth Whales*, *The Retail Trap*, and *Market Noise*).

An empirical **Walk-Forward Model Calibration Engine** evaluates live forward returns ($T+5, T+15, T+30$) against the S&P 500 (`SPY`) benchmark, presenting live cohort maturation scorecards and mathematically tuning scoring weights across all engines via an interactive `/calibration` dashboard.

---

## Architecture Diagram

```mermaid
graph TD
    subgraph SOURCES["Data Sources & Ingestion"]
        A["Reddit OAuth API"] --> RAW_SOC[("retail_social_raw")]
        B1["SEC Form 4 OpenInsider / yfinance"] --> RAW_INS[("insider_trades_raw")]
        B2["STOCK Act PTR Disclosures"] --> RAW_CONG[("congress_trades_raw")]
        C["Option Chains & Sweeps"] --> RAW_OPT[("options_whale_raw")]
        D["yfinance Metrics + SEC 10-Q/8-K"] --> RAW_CORE[("core_equity_raw")]
    end

    subgraph RAW_LAYER["Layer 1: Raw Audit Tables"]
        RAW_SOC
        RAW_INS
        RAW_CONG
        RAW_OPT
        RAW_CORE
    end

    subgraph REPORT_LAYER["Layer 2: Synthesized Reports & Overlays"]
        RAW_CORE -->|Ground Truth Synthesis| REP_CORE[("core_equity_reports")]
        RAW_SOC -->|Retail Hype Scoring| REP_RET[("retail_sentiment_reports")]
        REP_CORE --> REP_RET
        RAW_INS -->|Inflow Cluster Scoring| REP_SM[("smart_money_reports")]
        RAW_CONG --> REP_SM
        REP_CORE --> REP_SM
        RAW_OPT -->|Volume/OI & Call Sweeps| REP_OPT[("options_whale_reports")]
        REP_CORE --> REP_OPT
        REP_RET -->|3-Way Cross-Engine Correlator| REP_SYN[("synthesis_reports")]
        REP_SM --> REP_SYN
        REP_OPT --> REP_SYN
    end

    subgraph CALIB["Model Calibration & Backtesting"]
        REP_CORE --> BACKTEST["Backtest & Calibration Engine<br/>backtest_engine.py"]
        REP_SYN --> BACKTEST
        BACKTEST -->|T+30 Excess Alpha vs SPY| CALIB_DB[("model_calibration_runs")]
        BACKTEST -->|Tuned Weights| WEIGHTS_REG["Scoring Weights Registry<br/>scoring_weights.py"]
    end

    subgraph BACKEND["Backend API (FastAPI)"]
        REP_CORE --> API["FastAPI Server<br/>main.py"]
        REP_RET --> API
        REP_SM --> API
        REP_OPT --> API
        REP_SYN --> API
        CALIB_DB --> API
    end

    subgraph FRONTEND["Frontend Dashboard (Next.js)"]
        API --> DASH["Retail Momentum Feed<br/>/"]
        API --> SM["Smart Money Inflow Feed<br/>/smart-money"]
        API --> SYN_PAGE["Synthesis Matrix<br/>/synthesis"]
        API --> HIST["Historical Archives<br/>/stats"]
        API --> MASTER_REP["Unified Master Equity Report<br/>/report/:ticker"]
        API --> CALIB_PAGE["Model Calibration & Scorecard<br/>/calibration"]
        API --> ANALYTICS["Ticker Analytics & Archetype Lifecycle<br/>/analytics"]
    end
```

---

## Project Structure

```
stock-picker/
├── backend/
│   ├── app/
│   │   ├── agent.py                 # Pydantic AI agent for retail reports & trajectory meta-analyses
│   │   ├── backtest_engine.py       # Walk-forward alpha computation (T+5, T+15, T+30 vs SPY) & live maturation tracker
│   │   ├── core_intel_engine.py     # Decoupled Core Equity Intelligence researcher & 6-hr cache
│   │   ├── crud.py                  # Async SQLAlchemy CRUD operations & multi-table date aggregation
│   │   ├── database.py              # Engine & async SQLite session management (anchored to backend/stock_analyzer.db)
│   │   ├── llm_schemas.py           # Pydantic schemas (CoreIntelSynthesis, RetailOverlay, SmartMoneyReport)
│   │   ├── main.py                  # FastAPI endpoints & Unified Master Report aggregator
│   │   ├── market_researcher.py     # yfinance & DuckDuckGo metrics, news fetcher, and ticker validator
│   │   ├── models.py                # Dual-layer SQLAlchemy models: Layer 1 Raw (*_raw) & Layer 2 Reports (*_reports)
│   │   ├── options_pipeline.py      # Engine 3 orchestrator for Institutional Whale Options Radar
│   │   ├── options_scraper.py       # yfinance option chain scanner for unusual Volume > 2.5x OI & sweeps
│   │   ├── options_scorer.py        # Whale Conviction Scorer (0-100) & put/call volume skew calculator
│   │   ├── retail_pipeline.py       # Engine 1 orchestrator for Retail Momentum Scout
│   │   ├── pipeline.py              # Full multi-engine pipeline orchestrator (Engine 1 + 2 + 3 + Synthesis)
│   │   ├── reddit_scraper.py        # Multi-subreddit Reddit OAuth API client (Client Credentials)
│   │   ├── scheduler.py             # APScheduler cron job orchestrating discovery, core intel, & synthesis
│   │   ├── scoring_weights.py       # Centralized dynamic weights registry with persistence
│   │   ├── smart_money_ingestor.py  # Market-wide SEC Form 4 (Code P) and Capitol Hill STOCK Act disclosures
│   │   ├── smart_money_pipeline.py  # Engine 2 orchestrator for Smart Money Inflow Overlay
│   │   ├── smart_money_researcher.py# Gemini-driven government contract & swing catalyst researcher
│   │   ├── smart_money_scorer.py    # Multi-factor conviction scoring & committee alignment matrix
│   │   ├── synthesis_engine.py      # 3-Way Triangulation matrix correlator (The Rocket, Retail Trap, Silent Accumulation)
│   │   ├── telegram_notifier.py     # Telegram Bot API client with deduplication cache
│   │   └── ticker_extractor.py      # Regex extraction, noise blacklist filtering, and engagement scoring
│   ├── scripts/
│   │   └── reset_and_run.py         # Full database wipe & end-to-end multi-engine execution
│   ├── tests/
│   │   ├── test_analytics_api.py    # Async integration tests for dates & analytics endpoints
│   │   ├── test_api_endpoints.py    # Symmetrical namespaced endpoints (/api/retail, /api/master, /api/smart-money)
│   │   ├── test_core_intel_and_tabs.py # Tests for Core Intel caching, candidate deduplication, & historical tab APIs
│   │   ├── test_evals.py            # LLM evaluation and ticker validation tests
│   │   ├── test_options_and_calibration.py # Tests for options scoring, backtest alpha math, and weights registry
│   │   ├── test_smart_money.py      # Form 4 extraction, smart money serialization & guardrails
│   │   ├── test_smart_money_political.py # Engine 2 scoring, committee mapping & archetype tests
│   │   └── test_telegram_notifier.py# Telegram digest formatting & dispatch tests
│   ├── pyproject.toml               # Backend dependencies (managed via uv)
│   ├── run_pipeline.py              # CLI script to execute full pipeline (Engine 1 + Engine 2 + Engine 3 + Synthesis)
│   ├── send_test_telegram.py        # CLI tool to test or manually dispatch today's digest
│   └── query_report.py              # CLI tool to inspect a report from the database
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Homepage: Retail Momentum top stocks
│   │   │   ├── calibration/page.tsx # Live Walk-Forward Maturation Tracker (T+5/T+15/T+30 vs SPY, cohort stream, hyperparameter tuning)
│   │   │   ├── retail/[ticker]/     # Retail Momentum Report: Engine 1 signals + Core Intel
│   │   │   ├── smart-money/         # Smart Money & Gov: Market-wide radar & catalyst reports
│   │   │   │   ├── page.tsx         # Inflow Feed & ranked candidates
│   │   │   │   └── [ticker]/page.tsx# Smart Money Catalyst Report: Inflow ledger + Core Intel
│   │   │   ├── synthesis/page.tsx   # Cross-Engine Synthesis Matrix & Retail Awareness Gauge
│   │   │   ├── stats/page.tsx       # Historical Reports explorer: 3 Dedicated Tabs (Retail, Smart Money, Synthesis)
│   │   │   ├── analytics/page.tsx   # Multi-run Ticker Analytics, trajectory chart & Archetype Lifecycle
│   │   │   └── report/[ticker]/     # Unified Master Report: Contrarian Playbook + Core Intel + Institutional Capital Flow (Inflow & Outflow Ledgers) + Options Flow Card
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Persistent top navigation bar across all 6 sections
│   │   │   ├── OptionsFlowCard.tsx  # Whale Options Radar card: Volume/OI ratio, OTM call sweeps, and put/call skew
│   │   │   ├── ContrarianPlaybook.tsx # Cross-Engine Divergence Heatmap, execution tactics & lifecycle vector
│   │   │   ├── SmartMoneyRadar.tsx  # Form 4 executive flow & Capitol Hill disclosures
│   │   │   ├── PriceTrajectoryChart.tsx # SVG chart of Market Price vs Target Price
│   │   │   ├── MetaAnalysisCard.tsx # On-demand AI Trajectory Meta-Analysis
│   │   │   ├── ArchetypeLifecycleTimeline.tsx # Multi-run synthesis archetype migration timeline
│   │   │   ├── SentimentTrajectoryTimeline.tsx # Social sentiment evolution timeline
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
8. **Dual-Layer Relational Architecture (`_raw` vs `_reports`)**:
   - *Choice*: Separates immutable raw evidence tables (`core_equity_raw`, `retail_social_raw`, `insider_trades_raw`, `congress_trades_raw`, `options_whale_raw`) from synthesized intelligence reports (`core_equity_reports`, `retail_sentiment_reports`, `smart_money_reports`, `options_whale_reports`, `synthesis_reports`).
   - *Trade-off*: Slightly more granular tables, but enables zero data loss, exact auditability of LLM inputs, reusability of raw insider/congress data across future models, and seamless backtesting with zero frontend schema breakage.
9. **Strictly Normalized Overlays & Cross-Engine Trajectory Unification**:
   - *Choice*: `core_equity_reports` is the canonical owner of corporate fundamentals, ground truth status, SEC disclosures, and risk profiles. Specialized report overlays (`retail_sentiment_reports`, `smart_money_reports`, `options_whale_reports`) reference `core_intel_id` without duplicating ground truth or raw metric columns. Multi-run trajectory analytics (`/api/analytics/ticker/{ticker}`) unify historical pipeline runs across all discovery engines and cross-engine synthesis states anchored by foundational core equity research records.
   - *Trade-off*: Requires relational joins and multi-table unification buckets, but guarantees cross-engine historical consistency, prevents data drift across reports, and ensures longitudinal AI meta-analysis has access to all pipeline runs regardless of which engine discovered the ticker.

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

## Canonical API Reference

| Domain | Endpoint | Method | Description |
|---|---|---|---|
| **Retail Momentum** | `/api/retail/today` | GET | Top retail momentum tickers from latest run |
| | `/api/retail/reports` | GET | Historical retail momentum reports by `?date=` |
| | `/api/retail/report/{ticker}` | GET | Detailed retail momentum report with linked Core Intel (supports `?date=YYYY-MM-DD`) |
| | `/api/retail/trigger` | POST | On-demand trigger for Engine 1 (Retail Momentum) |
| **Smart Money** | `/api/smart-money/today` | GET | Latest Form 4 & STOCK Act candidate tickers |
| | `/api/smart-money/reports` | GET | Historical smart money reports by `?date=` |
| | `/api/smart-money/report/{ticker}` | GET | Self-contained smart catalyst report + Core Intel + Inflow Ledger (supports `?date=YYYY-MM-DD`) |
| | `/api/smart-money/trigger` | POST | On-demand trigger for Engine 2 (Smart Money Scout) |
| **Whale Options** | `/api/options/today` | GET | Latest unusual options flow and call sweep candidates |
| | `/api/options/reports` | GET | Historical options whale reports by `?date=` |
| | `/api/options/report/{ticker}` | GET | Detailed ticker options flow ledger + Core Intel (supports `?date=YYYY-MM-DD`) |
| | `/api/options/trigger` | POST | On-demand trigger for Engine 3 (Whale Options Radar) |
| **Synthesis & Master** | `/api/synthesis/today` | GET | Cross-engine 3-way archetype synthesis matrix records |
| | `/api/synthesis/reports` | GET | Historical synthesis matrix records by `?date=` |
| | `/api/master/report/{ticker}` | GET | Unified Master Report with Contrarian Playbook & multi-engine overlays (supports `?date=YYYY-MM-DD`) |
| | `/api/master/report/{ticker}/text` | GET | Plain-text summary for notifications/bots |
| **Calibration & Backtest** | `/api/calibration/scorecard` | GET | Walk-forward hit rates (T+30 vs SPY), archetype stats, and weight tuning |
| | `/api/calibration/apply-weights` | POST | Persist approved calibrated weights into production configuration |
| **Dates & Analytics** | `/api/dates` | GET | Distinct generated report dates across all engines |
| | `/api/analytics/tickers` | GET | Distinct tracked tickers across all engines |
| | `/api/analytics/ticker/{ticker}` | GET | Historical multi-run trajectory series |
| | `/api/analytics/ticker/{ticker}/archetypes` | GET | Chronological synthesis archetype progression |
| | `/api/analytics/ticker/{ticker}/meta-analysis` | GET/POST | Trajectory meta-analysis (retrieval & on-demand generation) |
| **Scheduler & Health** | `/health` | GET | Health check status |
| | `/api/scheduler/status` | GET | Live background scheduler status, registered jobs, and next run times |


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

