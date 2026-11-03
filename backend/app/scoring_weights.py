import json
import copy
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "calibrated_weights.json"

DEFAULT_WEIGHTS: Dict[str, Dict[str, Any]] = {
    "retail": {
        "post_score_weight": 1.0,
        "comment_score_weight": 1.0,
        "min_mention_floor": 2,
        "buy_upside_min_pct": 15.0,
    },
    "smart_money": {
        "c_suite_weight": 3.0,
        "director_weight": 2.0,
        "officer_weight": 1.0,
        "cluster_3_plus_multiplier": 2.5,
        "cluster_2_multiplier": 1.5,
        "dollar_vol_divisor": 50000.0,
        "dollar_vol_cap_points": 50.0,
        "committee_match_multiplier": 3.0,
        "conviction_tier_high": 150.0,
        "conviction_tier_moderate": 75.0,
    },
    "options_whale": {
        "min_volume_oi_ratio": 2.5,
        "min_premium_threshold": 100000.0,
        "otm_call_max_dte": 45,
        "otm_call_min_dte": 7,
        "put_call_ratio_bullish_cutoff": 0.6,
    },
    "synthesis": {
        "stealth_timing_edge_base": 95.0,
        "retail_decay_multiplier": 2.0,
        "rocket_timing_edge": 50.0,
        "retail_trap_timing_edge": 15.0,
    },
}


def get_active_weights() -> Dict[str, Dict[str, Any]]:
    """Returns active parameter weights, loading persistent calibrated overrides if available."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Deep merge with defaults to ensure all keys exist
                merged = copy.deepcopy(DEFAULT_WEIGHTS)
                for section, vals in data.items():
                    if section in merged and isinstance(vals, dict):
                        merged[section].update(vals)
                return merged
        except Exception as e:
            logger.warning(f"Failed to load calibrated weights from {CONFIG_PATH}: {e}. Using defaults.")
    return copy.deepcopy(DEFAULT_WEIGHTS)


def update_active_weights(new_weights: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Persists calibrated parameter overrides into the local config file."""
    current = get_active_weights()
    for section, vals in new_weights.items():
        if section in current and isinstance(vals, dict):
            current[section].update(vals)
        elif isinstance(vals, dict):
            current[section] = vals

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

    logger.info(f"Successfully updated active weights in {CONFIG_PATH}")
    return current


def reset_weights_to_default() -> Dict[str, Dict[str, Any]]:
    """Resets weights to hardcoded defaults and removes config file."""
    if CONFIG_PATH.exists():
        try:
            CONFIG_PATH.unlink()
        except Exception as e:
            logger.error(f"Error removing {CONFIG_PATH}: {e}")
    return copy.deepcopy(DEFAULT_WEIGHTS)


def get_smart_money_weights() -> Dict[str, Any]:
    return get_active_weights()["smart_money"]


def get_retail_weights() -> Dict[str, Any]:
    return get_active_weights()["retail"]


def get_options_weights() -> Dict[str, Any]:
    return get_active_weights()["options_whale"]


def get_synthesis_weights() -> Dict[str, Any]:
    return get_active_weights()["synthesis"]
