# Subreddit Stock Analyzer - Frontend

This is the frontend dashboard for the Subreddit Stock Analyzer. It provides a clean, responsive UI to view daily trending stocks extracted from Reddit and the AI-generated analysis reports for each.

## Architecture & Overview

- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Data Fetching:** Standard `fetch` API connecting to the local FastAPI backend.

The frontend is kept intentionally simple and lightweight for the MVP:
- `/`: The main dashboard displaying the top stocks of the day, their rank, and engagement scores.
- `/report/[ticker]`: A detailed view displaying the AI-generated industry overview, news summary, Reddit sentiment, and final Buy/Sell/Hold recommendation.
- `/stats`: A historical overview of ticker mentions over time.

## Local Setup

### Prerequisites
- Node.js (v18+)
- `npm` or `yarn`

### Installation

1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```

## How to Run

1. Ensure the Python FastAPI backend is running on `localhost:8000`.
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open your browser to `http://localhost:3000`.

## How to Test

For the MVP, there are no comprehensive unit tests set up for the frontend components. You can verify the UI manually by:
1. Running the backend pipeline script to seed the database with mock or live data.
2. Navigating through the dashboard, detailed report, and statistics pages.
