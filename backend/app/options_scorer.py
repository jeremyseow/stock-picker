import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def score_options_flow(opt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a normalized Whale Conviction Score (0.0 to 100.0) based on
    volume-over-open-interest spikes, aggressive OTM call premium, and put/call ratio skew.
    """
    ticker = opt_data.get("ticker", "").upper()
    peak_oi = float(opt_data.get("peak_oi_ratio", 1.0))
    net_prem = float(opt_data.get("net_bullish_premium", 0.0))
    pc_ratio = float(opt_data.get("put_call_ratio", 1.0))
    unusual = opt_data.get("unusual_contracts", [])

    # 1. Volume/OI factor (up to 35 points)
    oi_points = min(peak_oi * 7.0, 35.0)

    # 2. Bullish Sweep Premium factor (up to 40 points: $1M spent gives full points)
    prem_points = min((net_prem / 25000.0), 40.0)

    # 3. Put/Call Ratio Skew factor (up to 25 points if heavy call skew)
    # If P/C is 0.2 -> 20 pts; if P/C is 1.0 or higher -> 0 pts
    skew_points = max(0.0, (1.0 - min(pc_ratio, 1.0)) * 25.0)

    total_score = round(min(oi_points + prem_points + skew_points, 100.0), 2)

    # Top strike summary
    top_sweeps = [c for c in unusual if c.get("is_sweep")]
    if not top_sweeps and unusual:
        top_sweeps = unusual

    summaries = []
    for c in top_sweeps[:2]:
        strike_val = c.get("strike", 0)
        exp_val = c.get("expiration", "")
        ratio_val = c.get("ratio", 1.0)
        prem_val = c.get("premium", 0)
        prem_str = f"${int(prem_val / 1000)}k" if prem_val >= 1000 else f"${int(prem_val)}"
        summaries.append(f"${strike_val}C {exp_val} ({ratio_val}x OI, {prem_str})")

    top_summary = ", ".join(summaries) if summaries else "Standard options volume"

    if total_score >= 70.0:
        sentiment_bias = "Extremely Bullish Sweeps"
    elif total_score >= 40.0:
        sentiment_bias = "Moderate Bullish Accumulation"
    elif pc_ratio > 1.2:
        sentiment_bias = "Cautious / Put Skew"
    else:
        sentiment_bias = "Neutral Tape"

    return {
        "ticker": ticker,
        "whale_score": total_score,
        "unusual_oi_multiplier": peak_oi,
        "put_call_ratio": pc_ratio,
        "net_bullish_premium": net_prem,
        "sentiment_bias": sentiment_bias,
        "top_strike_summary": top_summary,
        "unusual_contracts": unusual,
        "current_price": opt_data.get("current_price", 0.0),
    }


def rank_whale_candidates(options_records: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """Ranks options candidates by Whale Conviction Score descending."""
    scored = [score_options_flow(r) for r in options_records]
    # Filter candidates that have meaningful activity (whale_score > 0)
    filtered = [s for s in scored if s["whale_score"] > 0]
    filtered.sort(key=lambda x: x["whale_score"], reverse=True)

    ranked = []
    for idx, item in enumerate(filtered[:limit], 1):
        item["rank"] = idx
        ranked.append(item)
    return ranked

