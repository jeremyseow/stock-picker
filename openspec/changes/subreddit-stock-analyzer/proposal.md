## Why

Currently, discovering highly discussed stocks on Reddit and manually researching their potential is a time-consuming daily process. This change introduces an automated daily pipeline to identify trending stocks on a specified subreddit, perform deep market research on them, and present actionable insights (buy/sell recommendations, sentiment, news, etc.) in a centralized dashboard. This allows for quick, data-driven investment decisions based on social sentiment without manual effort.

## What Changes

- Create a daily scheduled background job that scrapes a specified subreddit for trending stock tickers.
- Develop a market research service that queries external APIs (news, financial data) for each identified stock to analyze its industry, recent events, sentiment, and growth potential.
- Implement a report generation engine to synthesize the research into a concise summary, including a buy/sell recommendation.
- Build a separate frontend dashboard application to display these generated reports and overall trending stock statistics.

## Capabilities

### New Capabilities
- `reddit-scraper`: A scheduled service to extract and aggregate highly discussed stock tickers from a target subreddit.
- `market-researcher`: A service responsible for aggregating market data, news, sentiment, and generating analytical reports with buy/sell indicators.
- `dashboard-frontend`: A web-based frontend to visualize daily stock reports and useful aggregate statistics.

### Modified Capabilities
- (None - this is a greenfield project)

## Impact

- **Backend Architecture**: Introduces new scheduled background jobs and integrations with third-party APIs (Reddit API, financial data providers, news APIs, and potentially LLM for report generation).
- **Frontend Architecture**: Requires bootstrapping a new dashboard web application (React, Next.js, or similar).
- **Data Storage**: Requires a database or storage solution for persisting scraped stock data and generated reports for historical view.
