## Context

See `proposal.md` for motivation. Currently, `GET /api/smart-money/report/{ticker}` returns only Form 4 transactions and catalyst notes without the ticker's fundamental valuation multiples and SEC ground truth. Additionally, the Synthesis Master Report repeats standard 4-panel data without highlighting what makes cross-engine synthesis unique: **divergence alpha and contrarian execution**. Finally, API routes use historical naming (`/api/reports` vs. `/api/smart-money`).

## Goals / Non-Goals

**Goals:**
- Make `/smart-money/[ticker]` completely self-contained by embedding Core Equity Intel (financial multiples, SEC 10-Q/8-K ground truth, corporate positioning, and risk profile).
- Provide a high-alpha **Divergence Scorecard** and **Actionable Contrarian Playbook** in the Master Report (`/report/[ticker]`), turning abstract archetype labels into concrete entry/exit/catalyst timing gameplans.
- Standardize backend endpoint namespacing (`/api/retail/...`, `/api/smart-money/...`, `/api/synthesis/...`, `/api/master/...`) with 100% backward compatibility for existing routes.

**Non-Goals:**
- Modifying the underlying database schema or adding new database tables (the existing `core_equity_intels`, `retail_reports`, `smart_money_reports`, and `synthesis_records` tables already store all necessary data).
- Modifying third-party ingestion logic or scraping frequencies.

## Decisions

### Decision 1: Self-Contained Smart Catalyst API Payload
- `GET /api/smart-money/report/{ticker}` will fetch the `SmartMoneyReport` and its linked `CoreEquityIntel` (via `core_intel_id` or `get_latest_core_equity_intel`), returning both the Smart Money Inflow Ledger and the full Core Fundamentals & Ground Truth grid in a single response payload.
- *Alternatives considered*: Having the frontend fetch `/api/smart-money/report/{ticker}` and `/api/reports/{ticker}` simultaneously. Rejected because it doubles network overhead and leads to inconsistent loading states.

### Decision 2: Structured Archetype Contrarian Playbook Engine
- Implement a dedicated helper function (`generate_contrarian_playbook(archetype, timing_edge_score, retail_mentions, conviction_tier)`) returning structured tactical guidance:
  1. **Divergence Heatmap**: Comparative ratio of Retail Sentiment vs. Smart Money Conviction.
  2. **Entry Strategy**: Specific accumulation rules (e.g. stealth accumulation on volume dips vs. momentum swing with strict trailing stops vs. strictly avoid long positions).
  3. **Target Horizon**: Specific catalyst timeframe (e.g. 1–3 months pre-committee hearings vs. 2–4 weeks momentum ride).
  4. **Exit Signals**: Concrete liquidation triggers (e.g. retail hype saturation > 3x, Form 4 insider liquidation, or stop-loss trigger).
  5. **Lifecycle Vector**: Visual progression indicator through `Silent Accumulation ➔ The Rocket ➔ The Retail Trap ➔ Market Noise`.
- Render this playbook prominently at the top of the Synthesis section in `/report/[ticker]`.

### Decision 3: Backward-Compatible API Route Aliasing
- Introduce `/api/retail/reports` and `/api/retail/report/{ticker}` pointing to the Retail Momentum handlers, while retaining `/api/reports` and `/api/reports/{ticker}` for full backward compatibility.
- Expose `/api/master/report/{ticker}` as an explicit alias for `/api/reports/{ticker}`.

## Risks / Trade-offs

- **[Risk] Increased visual density on `/smart-money/[ticker]`** → *Mitigation*: Reuse the clean, collapsible/tabbed card design from `/report/[ticker]` to ensure readability.
- **[Risk] Route duplication causing divergence** → *Mitigation*: Both routes invoke the identical underlying async FastAPI handler function, ensuring zero divergence.

