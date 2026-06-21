## Context

The system requires an automated pipeline to scrape a specific subreddit for highly discussed stocks, perform market research, generate a daily report, and display it on a frontend dashboard. Currently, there is no existing infrastructure in this project for scheduled scraping, complex third-party API integration for financial data, report generation, or a standalone frontend dashboard.

## Goals / Non-Goals

**Goals:**
- Reliable daily extraction of trending stock tickers from a targeted subreddit.
- Integration with external APIs (e.g., news APIs, financial metrics APIs, and potentially LLMs) to generate comprehensive reports including industry insights, news, sentiment, and buy/sell signals.
- A responsive, easily accessible frontend dashboard to present the reports and related statistics clearly.
- Establish an evaluation framework to test the accuracy and consistency of LLM Buy/Sell recommendations.

**Non-Goals:**
- High-frequency trading or real-time (minute-by-minute) updates. The focus is on a daily digest.
- Creating a custom machine learning model for sentiment analysis from scratch (we will rely on existing APIs/LLMs).

## Decisions

**1. Backend Architecture: Python + Pydantic AI + FastMCP**
- *Decision*: The backend service will be built in Python, managed by `uv` for lightning-fast dependency resolution, leveraging Pydantic AI for structured LLM interactions and FastMCP for tooling/context injection.
- *Rationale*: Python is the industry standard for AI/LLM engineering. `uv` ensures reproducible and fast environment setups. Pydantic AI natively enforces structured outputs (crucial for our strict schemas), and the Python ecosystem offers unparalleled tools for LLM evaluations (e.g., Langfuse, Promptfoo, Ragas, Pytest) to ensure the model's Buy/Sell signals are consistent and accurate. 
- *Alternatives*: Golang + Gin was considered for sheer API performance, but Golang currently lacks mature, native LLM evaluation and structured output validation frameworks compared to Python. Because the core complexity of this app is LLM accuracy, Python is the clear winner.

**2. Scraping Mechanism: Direct JSON Endpoint Scraping (No Auth)**
- *Decision*: We will scrape Reddit's public `.json` endpoints directly (e.g., `/r/wallstreetbets/top.json`) using `httpx` with a custom User-Agent, bypassing the need for OAuth or PRAW. We will implement "polite delays" (e.g., `asyncio.sleep`) between requests to avoid rate limits. We will strictly limit scraping to the Top 20 posts and their Top 50 comments over the last 24 hours.
- *Rationale*: Eliminates the friction of API key management and simplifies deployment. Limiting the scope and adding deliberate sleep delays mitigates the risk of being blocked with a 429 Too Many Requests error.

**3. Report Generation & Prompting Strategy**
- *Decision*: Use an LLM (via Pydantic AI) to generate the report and summarize the raw Reddit comments. The prompt will enforce a strict "Default to HOLD" posture. A Buy or Sell signal will only be issued if overwhelming corroborating evidence exists across both financial data and social sentiment.
- *Rationale*: Protects against hallucinations and irrational meme-stock hype.

**4. Frontend Framework: Next.js**
- *Decision*: Use Next.js for the dashboard frontend.
- *Rationale*: Excellent rendering performance for dashboards and clear separation from the Python AI backend.

## Risks / Trade-offs

- **Risk: LLM Hallucinations / Inconsistent Advice** → *Mitigation*: We are implementing an LLM Eval framework natively in Python to run regressions on the prompts and ensure "Default to HOLD" works reliably.
- **Risk: Reddit Rate Limits (429 Errors)** → *Mitigation*: Scraping public `.json` endpoints without auth is heavily monitored. We will mitigate this by capping scrapes to Top 20 posts / 50 comments and adding deliberate sleep delays (e.g., 1.5s) between comment extraction requests to ensure polite scraping.
