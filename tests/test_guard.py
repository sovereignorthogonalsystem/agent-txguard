import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from guard import AgentTxGuard, GuardCondition, verify_route


def test_guard_passes_clean_conditions():
    guard = AgentTxGuard()
    conditions = [
        GuardCondition("a", True, "ok", weight=1.0),
        GuardCondition("b", True, "ok", weight=1.0),
    ]
    result = guard.evaluate(conditions, metadata={})
    assert result.decision == "PASS"
    assert result.safety_score == 1.0
    assert result.failed_conditions == []


def test_guard_blocks_critical_failure():
    guard = AgentTxGuard()
    conditions = [
        GuardCondition("safe", True, "ok", weight=1.0),
        GuardCondition("private_key_supplied", False, "key supplied", weight=5.0, severity="critical"),
    ]
    result = guard.evaluate(conditions, metadata={})
    assert result.decision == "BLOCK"
    assert "private_key_supplied" in result.failed_conditions


def test_route_blocks_bad_swap():
    payload = {
        "agent_id": "demo-agent-001",
        "chain": "solana",
        "intent": "swap",
        "nominal_profit_pct": 0.42,
        "estimated_fees_pct": 0.12,
        "estimated_slippage_pct": 0.38,
        "quote_age_seconds": 6.4,
        "liquidity_score": 0.52,
        "minimum_profit_pct": 0.25,
        "max_quote_age_seconds": 3.0,
        "minimum_liquidity_score": 0.7,
        "max_slippage_pct": 0.5,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }
    result = verify_route(payload)
    assert result.decision == "BLOCK"
    assert "positive_net_return" in result.failed_conditions
    assert "fresh_quote" in result.failed_conditions


def test_route_passes_clean_swap():
    payload = {
        "agent_id": "demo-agent-002",
        "chain": "solana",
        "intent": "swap",
        "nominal_profit_pct": 1.20,
        "estimated_fees_pct": 0.12,
        "estimated_slippage_pct": 0.18,
        "quote_age_seconds": 1.1,
        "liquidity_score": 0.91,
        "minimum_profit_pct": 0.25,
        "max_quote_age_seconds": 3.0,
        "minimum_liquidity_score": 0.7,
        "max_slippage_pct": 0.5,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }
    result = verify_route(payload)
    assert result.decision == "PASS"
    assert result.metadata["net_profit_pct"] == 0.9


def test_route_blocks_private_key_request():
    payload = {
        "agent_id": "unsafe-agent",
        "chain": "solana",
        "intent": "swap",
        "nominal_profit_pct": 2.0,
        "estimated_fees_pct": 0.1,
        "estimated_slippage_pct": 0.1,
        "quote_age_seconds": 1.0,
        "liquidity_score": 0.95,
        "private_key_supplied": True,
        "seed_phrase_supplied": False,
    }
    result = verify_route(payload)
    assert result.decision == "BLOCK"
    assert "non_custodial_request" in result.failed_conditions
