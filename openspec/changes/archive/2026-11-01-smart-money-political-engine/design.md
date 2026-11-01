## Context

See `proposal.md` for motivation. Currently, the application operates a single discovery engine (Engine 1) driven by Reddit discussions. We are introducing Engine 2 (Smart Money & Political Scout) as an independent pipeline alongside a Cross-Engine Synthesis Hub, providing distinct reports while keeping Engine 1 intact.

## Goals / Non-Goals

**Goals:**
- Ingest public market-wide SEC Form 4 open-market cash purchases (Code P) and Congressional STOCK Act Periodic Transaction Reports.
- Apply a multi-factor conviction scoring formula:
  - Role hierarchy: C-Suite (3.0x), Directors/10% owners (2.0x), Officers (1.0x).
  - Cluster multiplier: Up to 2.5x for $\ge 3$ insiders within 7 days.
  - Committee relevance multiplier: 3.0x when politician's committee oversees the ticker's industry.
  - Freshness decay penalty: Scaling down trades older than 15 days.
- Dispatch an LLM research agent on top 5 smart money candidates to investigate government contracts, bills, regulatory approvals, and swing catalyst horizons.
- Build a Cross-Engine Synthesis module mapping stocks into 4 archetypes: The Rocket, The Retail Trap, Silent Accumulation, and Market Noise.
- Expose three distinct frontend surfaces: Retail Momentum (`/`), Smart Money & Gov (`/smart-money`), and Synthesis Matrix (`/synthesis`).

**Non-Goals:**
- Paid enterprise API dependencies (leverage free open SEC EDGAR / OpenInsider feeds and House/Senate Stock Watcher JSON endpoints).
- Live intraday algorithmic execution.
- Modifying Engine 1's existing recommendation logic or daily report structure.

## Decisions

### Decision 1: Modular Dual-Pipeline Architecture
- **Choice**: Implement Engine 2 in dedicated modules (`smart_money_ingestor.py`, `smart_money_scorer.py`, `smart_money_pipeline.py`), orchestrated alongside Engine 1.
- **Rationale**: Keeps Engine 1 completely decoupled. If SEC filings are delayed or an external feed blips, Engine 1 runs unaffected.
- **Alternative considered**: Forcing all logic into a single monolithic pipeline. Rejected due to tight coupling and mismatched ingestion cadences.

### Decision 2: Deterministic Pre-Filtering Before LLM Research
- **Choice**: Compute math-based Conviction Scores across hundreds of ingested transactions to isolate exactly the top 5 candidates before invoking the LLM research agent.
- **Rationale**: Minimizes token usage and costs by reserving LLM synthesis exclusively for the highest-conviction signals.

### Decision 3: Committee-to-Sector Relevance Matrix
- **Choice**: Maintain a static mapping dictionary:
  - Armed Services, Intelligence, Foreign Affairs $\rightarrow$ Defense & Aerospace (`LMT`, `RTX`, `PLTR`, `GD`).
  - Energy & Natural Resources, Environment $\rightarrow$ Energy & Utilities (`XOM`, `CVX`, `FSLR`, `CEG`).
  - Banking, Financial Services, Finance $\rightarrow$ Financials (`JPM`, `GS`, `KRE`).
  - Health, HELP $\rightarrow$ Healthcare & Biotech (`PFE`, `LLY`, `MRK`).
  - Commerce, Science, Transportation $\rightarrow$ Technology & Semis (`NVDA`, `TSMC`, `QCOM`).
- **Rationale**: Programmatic, lightning-fast identification of political alpha.

### Decision 4: Dedicated SQLite Tables for Engine 2 & Synthesis
- **Choice**: Create `SmartMoneyTicker`, `SmartMoneyReport`, and `SynthesisRecord` models in `backend/app/models.py`.
- **Rationale**: Maintains clean relational isolation from Engine 1's `DailyTicker` and `TickerReport` tables, preventing schema bloat or migration conflicts.

## Risks / Trade-offs

- [Risk] Congressional 45-day reporting lag → [Mitigation] Freshness decay penalty down-weights older filings; LLM research verifies whether the legislative catalyst has already passed or remains in play.
- [Risk] Formula sensitivity requires benchmarking → [Mitigation] Configurable scoring weights stored in a dedicated configuration object so parameters can be tuned dynamically.
- [Risk] Duplicate tickers between Engine 1 and Engine 2 → [Mitigation] Handled naturally by the Cross-Engine Synthesis module, which specifically highlights overlapping tickers as "The Rocket" or "The Retail Trap".

