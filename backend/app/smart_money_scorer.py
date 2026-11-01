import logging
from collections import defaultdict
from typing import List, Dict, Any
from app.market_researcher import is_valid_ticker

logger = logging.getLogger(__name__)

# Sector to Committee relevance mapping
COMMITTEE_SECTOR_MAP = {
    "Technology": ["commerce", "science", "intelligence", "judiciary", "telecom"],
    "Communication Services": ["commerce", "telecom", "judiciary"],
    "Industrials": ["armed services", "transportation", "commerce", "defense"],
    "Aerospace & Defense": ["armed services", "foreign affairs", "defense", "intelligence"],
    "Energy": ["energy", "natural resources", "environment", "interior"],
    "Healthcare": ["health", "help", "fda", "ways and means"],
    "Financial Services": ["banking", "finance", "financial services", "budget"],
    "Basic Materials": ["natural resources", "commerce", "agriculture"],
}


def get_role_weight(title: str) -> float:
    """Returns weight based on insider seniority hierarchy."""
    if not title:
        return 1.0
    t = title.upper()
    if any(k in t for k in ["CEO", "CHIEF EXECUTIVE", "CFO", "CHIEF FINANCIAL", "COO", "CHAIRMAN", "PRESIDENT"]):
        return 3.0
    if any(k in t for k in ["DIR", "DIRECTOR", "10%", "BENEFICIAL"]):
        return 2.0
    return 1.0


def get_cluster_multiplier(unique_insiders_count: int) -> float:
    """Multiplies conviction when multiple distinct insiders buy together."""
    if unique_insiders_count >= 3:
        return 2.5
    if unique_insiders_count == 2:
        return 1.5
    return 1.0


def score_insider_trades(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregates and scores Form 4 insider purchases per ticker.
    Formula: Total Value Norm * Max Role Weight * Cluster Multiplier * Position Growth Factor.
    """
    by_ticker = defaultdict(list)
    for t in trades:
        by_ticker[t["ticker"].upper()].append(t)

    scores = {}
    for ticker, t_list in by_ticker.items():
        total_val = sum(t["value"] for t in t_list)
        unique_buyers = set(t["insider_name"] for t in t_list)
        max_role = max(get_role_weight(t["title"]) for t in t_list)
        cluster_mult = get_cluster_multiplier(len(unique_buyers))
        max_delta = max((t["delta_own"] for t in t_list if t.get("delta_own")), default=0.0)
        growth_factor = 1.0 + min(max_delta, 2.0)  # Capped at 3.0x

        # Normalize dollar value (every $50k is 1 base point, capped at 50 points)
        val_points = min(total_val / 50000.0, 50.0)
        insider_score = round(val_points * max_role * cluster_mult * growth_factor, 2)

        buyer_titles = [f"{t['insider_name']} ({t['title']})" for t in t_list[:3]]
        summary = ", ".join(buyer_titles)
        if len(t_list) > 3:
            summary += f" +{len(t_list) - 3} more"

        scores[ticker] = {
            "ticker": ticker,
            "insider_score": insider_score,
            "total_buy_volume": total_val,
            "cluster_count": len(unique_buyers),
            "top_buyer_summary": summary,
            "insider_trades": t_list,
        }

    return scores


def score_congressional_trades(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Scores Congressional trades based on trade size bracket and committee relevance.
    """
    by_ticker = defaultdict(list)
    for t in trades:
        by_ticker[t["ticker"].upper()].append(t)

    scores = {}
    for ticker, t_list in by_ticker.items():
        pol_score = 0.0
        details = []

        for t in t_list:
            amt = t.get("amount_range", "")
            base = 10.0
            if any(k in amt for k in ["$250k", "$500k", "$1M", "$1,000,000", "$500,001"]):
                base = 35.0
            elif any(k in amt for k in ["$50k", "$100k", "$100,001", "$50,001"]):
                base = 20.0

            # Default committee multiplier: 1.5x (can be boosted during full research)
            comm_mult = 1.5
            pol_score += base * comm_mult
            details.append(f"{t.get('politician', 'Member')} ({amt})")

        scores[ticker] = {
            "ticker": ticker,
            "political_score": round(pol_score, 2),
            "political_summary": ", ".join(details[:3]),
            "congress_trades": t_list,
        }

    return scores


def rank_smart_money_candidates(
    insider_trades: List[Dict[str, Any]],
    congress_trades: List[Dict[str, Any]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Combines insider scores and political scores to rank top smart money candidates.
    Validates that each candidate is a valid, tradeable stock ticker via yfinance.
    """
    insider_scores = score_insider_trades(insider_trades)
    congress_scores = score_congressional_trades(congress_trades)

    all_tickers = set(insider_scores.keys()) | set(congress_scores.keys())
    combined = []

    for ticker in all_tickers:
        i_data = insider_scores.get(ticker, {})
        p_data = congress_scores.get(ticker, {})

        i_score = i_data.get("insider_score", 0.0)
        p_score = p_data.get("political_score", 0.0)
        total_conviction = round(i_score + p_score, 2)

        # Build ledger summary
        summary_parts = []
        if i_data.get("top_buyer_summary"):
            summary_parts.append(f"Insiders: {i_data['top_buyer_summary']}")
        if p_data.get("political_summary"):
            summary_parts.append(f"Congress: {p_data['political_summary']}")

        combined.append({
            "ticker": ticker,
            "conviction_score": total_conviction,
            "insider_score": i_score,
            "political_score": p_score,
            "cluster_count": i_data.get("cluster_count", 0),
            "total_buy_volume": i_data.get("total_buy_volume", 0.0),
            "top_buyer_summary": " | ".join(summary_parts),
            "insider_trades": i_data.get("insider_trades", []),
            "congress_trades": p_data.get("congress_trades", []),
        })

    # Sort descending by conviction score
    ranked = sorted(combined, key=lambda x: x["conviction_score"], reverse=True)

    # Filter for valid tickers
    valid_candidates = []
    for c in ranked:
        if is_valid_ticker(c["ticker"]):
            valid_candidates.append(c)
            if len(valid_candidates) >= limit:
                break

    logger.info(f"Selected top {len(valid_candidates)} smart money tickers: {[c['ticker'] for c in valid_candidates]}")
    return valid_candidates

