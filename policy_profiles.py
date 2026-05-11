from __future__ import annotations

from typing import Any, Dict


POLICY_PROFILES: Dict[str, Dict[str, Any]] = {
    "conservative": {
        "description": "Strict safety profile for fragile or high-value autonomous actions.",
        "minimum_profit_pct": 0.50,
        "max_quote_age_seconds": 2.0,
        "minimum_liquidity_score": 0.85,
        "max_slippage_pct": 0.25,
        "max_slippage_bps": 25,
        "max_price_impact_pct": 0.25,
        "max_time_taken": 0.25,
        "max_slot_lag": 75,
        "max_compute_units": 150000,
        "max_fee_lamports": 5000,
    },
    "balanced": {
        "description": "Default profile for normal agent preflight checks.",
        "minimum_profit_pct": 0.25,
        "max_quote_age_seconds": 3.0,
        "minimum_liquidity_score": 0.70,
        "max_slippage_pct": 0.50,
        "max_slippage_bps": 50,
        "max_price_impact_pct": 0.50,
        "max_time_taken": 0.50,
        "max_slot_lag": 150,
        "max_compute_units": 200000,
        "max_fee_lamports": 10000,
    },
    "aggressive": {
        "description": "Higher-risk profile for agents willing to tolerate more execution variance.",
        "minimum_profit_pct": 0.10,
        "max_quote_age_seconds": 5.0,
        "minimum_liquidity_score": 0.55,
        "max_slippage_pct": 1.00,
        "max_slippage_bps": 100,
        "max_price_impact_pct": 1.00,
        "max_time_taken": 1.00,
        "max_slot_lag": 300,
        "max_compute_units": 300000,
        "max_fee_lamports": 25000,
    },
}


def get_policy_profile(name: str | None) -> Dict[str, Any]:
    profile_name = (name or "balanced").lower().strip()
    profile = POLICY_PROFILES.get(profile_name, POLICY_PROFILES["balanced"]).copy()
    profile["profile"] = profile_name if profile_name in POLICY_PROFILES else "balanced"
    return profile


def list_policy_profiles() -> Dict[str, Dict[str, Any]]:
    return POLICY_PROFILES
