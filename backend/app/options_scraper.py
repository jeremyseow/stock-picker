import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import yfinance as yf
from app.scoring_weights import get_options_weights

logger = logging.getLogger(__name__)


def fetch_options_data_for_ticker(ticker: str) -> Dict[str, Any]:
    """
    Fetches option chains for a ticker using yfinance, identifying unusual volume
    relative to open interest (OI), OTM call sweeps, and put/call volume skews.
    """
    clean_ticker = ticker.strip().upper()
    weights = get_options_weights()
    min_vol_oi = float(weights.get("min_volume_oi_ratio", 2.5))
    min_prem = float(weights.get("min_premium_threshold", 100000.0))
    min_dte = int(weights.get("otm_call_min_dte", 7))
    max_dte = int(weights.get("otm_call_max_dte", 45))

    empty_result = {
        "ticker": clean_ticker,
        "current_price": 0.0,
        "total_call_volume": 0,
        "total_put_volume": 0,
        "put_call_ratio": 1.0,
        "unusual_contracts": [],
        "peak_oi_ratio": 1.0,
        "net_bullish_premium": 0.0,
    }

    try:
        t = yf.Ticker(clean_ticker)
        expirations = t.options
        if not expirations:
            logger.debug(f"No option chains available for ${clean_ticker}")
            return empty_result

        # Retrieve current price
        fast_info = getattr(t, "fast_info", None)
        current_price = getattr(fast_info, "last_price", 0.0) or 0.0
        if current_price <= 0.0:
            hist = t.history(period="1d")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])

        now_date = datetime.now(timezone.utc).date()
        unusual_contracts: List[Dict[str, Any]] = []
        total_call_vol = 0
        total_put_vol = 0
        net_bullish_prem = 0.0
        peak_oi_ratio = 1.0

        for exp in expirations:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                dte = (exp_date - now_date).days
                if dte < 0:
                    continue

                chain = t.option_chain(exp)
                calls_df = chain.calls
                puts_df = chain.puts

                if not calls_df.empty:
                    c_vol = int(calls_df["volume"].fillna(0).sum())
                    total_call_vol += c_vol

                    for _, row in calls_df.iterrows():
                        vol = int(row.get("volume") or 0)
                        oi = int(row.get("openInterest") or 0)
                        strike = float(row.get("strike") or 0.0)
                        last_price = float(row.get("lastPrice") or 0.0)
                        bid = float(row.get("bid") or 0.0)
                        ask = float(row.get("ask") or 0.0)
                        mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else last_price
                        premium = vol * mid * 100.0

                        if oi > 0 and vol >= min_vol_oi * oi and premium >= (min_prem / 2.0):
                            ratio = round(vol / oi, 2)
                            if ratio > peak_oi_ratio:
                                peak_oi_ratio = ratio

                            is_otm = current_price > 0 and strike > (current_price * 1.03)
                            is_sweep = is_otm and (min_dte <= dte <= max_dte) and premium >= min_prem
                            if is_sweep:
                                net_bullish_prem += premium

                            unusual_contracts.append({
                                "type": "CALL",
                                "strike": strike,
                                "expiration": exp,
                                "dte": dte,
                                "volume": vol,
                                "open_interest": oi,
                                "ratio": ratio,
                                "premium": round(premium, 2),
                                "is_otm": is_otm,
                                "is_sweep": is_sweep,
                            })

                if not puts_df.empty:
                    p_vol = int(puts_df["volume"].fillna(0).sum())
                    total_put_vol += p_vol

            except Exception as exp_err:
                logger.debug(f"Error reading option chain {exp} for {clean_ticker}: {exp_err}")
                continue

        # Sort unusual contracts by premium descending
        unusual_contracts.sort(key=lambda x: x["premium"], reverse=True)
        pc_ratio = round(total_put_vol / max(total_call_vol, 1), 2)

        return {
            "ticker": clean_ticker,
            "current_price": round(current_price, 2),
            "total_call_volume": total_call_vol,
            "total_put_volume": total_put_vol,
            "put_call_ratio": pc_ratio,
            "unusual_contracts": unusual_contracts[:10],
            "peak_oi_ratio": peak_oi_ratio,
            "net_bullish_premium": round(net_bullish_prem, 2),
        }

    except Exception as e:
        logger.warning(f"Failed to fetch options data for ${clean_ticker}: {e}")
        return empty_result

