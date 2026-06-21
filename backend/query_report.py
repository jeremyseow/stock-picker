import sys
import sqlite3
from datetime import datetime

def format_price(val):
    if val is None or val == "None" or val == "":
        return "N/A"
    try:
        return f"${float(val):.2f}"
    except ValueError:
        return str(val)

def query_report(ticker):
    conn = sqlite3.connect("stock_analyzer.db")
    cursor = conn.cursor()
    
    # Query the latest report for the ticker
    cursor.execute("""
        SELECT ticker, date, current_price, target_price,
               community_sentiment, community_hype,
               ground_truth_status, ground_truth_filings_news, events_happenings,
               reconciliation_risk_score, reconciliation_analysis, reconciliation_actionable_insight
        FROM ticker_reports
        WHERE UPPER(ticker) = ?
        ORDER BY date DESC
        LIMIT 1;
    """, (ticker.upper(),))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"Error: No report found for ticker '{ticker}' in the database.")
        sys.exit(1)
        
    (ticker, date_str, current_price, target_price,
     community_sentiment, community_hype,
     ground_truth_status, ground_truth_filings_news, events_happenings,
     reconciliation_risk_score, reconciliation_analysis, reconciliation_actionable_insight) = row
     
    # Parse date string to extract YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(date_str)
        formatted_date = dt.strftime("%Y-%m-%d")
    except Exception:
        formatted_date = str(date_str).split()[0]
        
    price_fmt = format_price(current_price)
    target_fmt = format_price(target_price)
    
    report_text = f"""Market Intelligence Report: {ticker}
Date: {formatted_date}
Price: {price_fmt} | Target: {target_fmt}

[COMMUNITY SENTIMENT]
- Sentiment: {community_sentiment}
- Hype: {community_hype}

[GROUND TRUTH]
- Status: {ground_truth_status}
- Filings/News: {ground_truth_filings_news}

[EVENTS & HAPPENINGS]
- Key Events: {events_happenings}

[RECONCILIATION]
- Risk Score: {reconciliation_risk_score}
- Analysis: {reconciliation_analysis}
- Actionable Insight: {reconciliation_actionable_insight}"""

    print(report_text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide a ticker symbol.")
        print("Usage: uv run python query_report.py <TICKER>")
        sys.exit(1)
        
    query_report(sys.argv[1])
