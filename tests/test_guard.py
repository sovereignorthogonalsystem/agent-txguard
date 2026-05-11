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


from guard import verify_simulation


def test_simulation_blocks_failed_transaction():
    payload = {
        "agent_id": "demo-agent-sim-block",
        "chain": "solana",
        "intent": "transaction",
        "simulation_ok": False,
        "simulation_error": "InstructionError: custom program error",
        "wallet_delta_lamports": -5000,
        "compute_units_used": 245000,
        "max_compute_units": 200000,
        "priority_fee_lamports": 25000,
        "max_priority_fee_lamports": 10000,
        "blockhash_age_slots": 180,
        "max_blockhash_age_slots": 120,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }

    result = verify_simulation(payload)

    assert result.decision == "BLOCK"
    assert "simulation_success" in result.failed_conditions
    assert "positive_wallet_delta" in result.failed_conditions
    assert "compute_unit_ceiling" in result.failed_conditions
    assert "fresh_blockhash" in result.failed_conditions


def test_simulation_passes_clean_transaction():
    payload = {
        "agent_id": "demo-agent-sim-pass",
        "chain": "solana",
        "intent": "transaction",
        "simulation_ok": True,
        "simulation_error": None,
        "wallet_delta_lamports": 125000,
        "compute_units_used": 142000,
        "max_compute_units": 200000,
        "priority_fee_lamports": 5000,
        "max_priority_fee_lamports": 10000,
        "blockhash_age_slots": 45,
        "max_blockhash_age_slots": 120,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }

    result = verify_simulation(payload)

    assert result.decision == "PASS"
    assert result.metadata["wallet_delta_lamports"] == 125000


from guard import verify_rpc_simulation_result


def test_rpc_simulation_result_blocks_rpc_error():
    payload = {
        "agent_id": "rpc-fail",
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "rpc_ok": False,
        "rpc_error": "RPC timeout",
        "value": {},
        "max_compute_units": 200000,
        "max_fee_lamports": 10000,
    }

    result = verify_rpc_simulation_result(payload)

    assert result.decision == "BLOCK"
    assert "rpc_call_success" in result.failed_conditions


def test_rpc_simulation_result_passes_clean_result():
    payload = {
        "agent_id": "rpc-pass",
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "rpc_ok": True,
        "rpc_error": None,
        "slot": 123,
        "value": {
            "err": None,
            "logs": ["Program 11111111111111111111111111111111 success"],
            "unitsConsumed": 120000,
            "fee": 5000
        },
        "max_compute_units": 200000,
        "max_fee_lamports": 10000,
    }

    result = verify_rpc_simulation_result(payload)

    assert result.decision == "PASS"
    assert result.metadata["units_consumed"] == 120000


def test_rpc_simulation_result_blocks_simulation_error():
    payload = {
        "agent_id": "rpc-sim-error",
        "rpc_url": "https://api.mainnet-beta.solana.com",
        "rpc_ok": True,
        "rpc_error": None,
        "slot": 123,
        "value": {
            "err": {"InstructionError": [0, "Custom"]},
            "logs": ["Program failed: custom program error"],
            "unitsConsumed": 180000,
            "fee": 5000
        },
        "max_compute_units": 200000,
        "max_fee_lamports": 10000,
    }

    result = verify_rpc_simulation_result(payload)

    assert result.decision == "BLOCK"
    assert "simulation_success" in result.failed_conditions
    assert "no_dangerous_logs" in result.failed_conditions


from guard import verify_jupiter_quote


def test_jupiter_quote_passes_clean_quote():
    payload = {
        "agent_id": "jupiter-pass",
        "current_slot": 299283800,
        "max_slippage_bps": 50,
        "max_price_impact_pct": 0.5,
        "max_time_taken": 0.5,
        "max_slot_lag": 150,
        "quote": {
            "inputMint": "So11111111111111111111111111111111111111112",
            "inAmount": "100000000",
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "outAmount": "16198753",
            "otherAmountThreshold": "16117760",
            "swapMode": "ExactIn",
            "slippageBps": 50,
            "platformFee": None,
            "priceImpactPct": "0.05",
            "routePlan": [{"swapInfo": {"label": "Demo AMM"}, "percent": 100}],
            "contextSlot": 299283763,
            "timeTaken": 0.015,
        },
    }

    result = verify_jupiter_quote(payload)

    assert result.decision == "PASS"
    assert result.metadata["routePlanLength"] == 1


def test_jupiter_quote_blocks_bad_quote():
    payload = {
        "agent_id": "jupiter-block",
        "current_slot": 299284000,
        "max_slippage_bps": 50,
        "max_price_impact_pct": 0.5,
        "max_time_taken": 0.5,
        "max_slot_lag": 150,
        "quote": {
            "inputMint": "So11111111111111111111111111111111111111112",
            "inAmount": "100000000",
            "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "outAmount": "0",
            "otherAmountThreshold": "0",
            "swapMode": "ExactIn",
            "slippageBps": 250,
            "platformFee": None,
            "priceImpactPct": "2.75",
            "routePlan": [],
            "contextSlot": 299283000,
            "timeTaken": 0.91,
        },
    }

    result = verify_jupiter_quote(payload)

    assert result.decision == "BLOCK"
    assert "positive_out_amount" in result.failed_conditions
    assert "slippage_policy" in result.failed_conditions
    assert "price_impact_policy" in result.failed_conditions
    assert "route_plan_present" in result.failed_conditions


def test_usage_meter_imports():
    from usage_meter import init_usage_db, usage_summary

    init_usage_db()
    summary = usage_summary()

    assert "total_events" in summary
    assert "by_endpoint" in summary
    assert "by_decision" in summary


def test_plan_policy_imports():
    from plans import get_active_plan, usage_policy_summary

    plan = get_active_plan()
    summary = usage_policy_summary()

    assert plan in ["free", "starter", "pro", "enterprise"]
    assert "monthly_limit" in summary
    assert "used_this_month" in summary
    assert "available_plans" in summary


def test_usage_meter_request_id_supports_summary():
    from usage_meter import log_usage_event, usage_summary

    result = {
        "request_id": "test-request-id",
        "decision": "PASS",
        "safety_score": 1.0,
        "metadata": {
            "agent_id": "test-agent",
            "request_id": "test-request-id"
        }
    }

    log_usage_event("/test/request-id", result, api_key_label="test")
    summary = usage_summary()

    assert "latest" in summary
    assert any(item.get("request_id") == "test-request-id" for item in summary["latest"])


def test_policy_profiles_imports():
    from policy_profiles import get_policy_profile, list_policy_profiles

    profiles = list_policy_profiles()
    conservative = get_policy_profile("conservative")
    unknown = get_policy_profile("does-not-exist")

    assert "balanced" in profiles
    assert conservative["profile"] == "conservative"
    assert unknown["profile"] == "balanced"


def test_conservative_policy_blocks_looser_route():
    from guard import verify_route

    payload = {
        "agent_id": "policy-test",
        "chain": "solana",
        "policy_profile": "conservative",
        "intent": "swap",
        "nominal_profit_pct": 0.40,
        "estimated_fees_pct": 0.05,
        "estimated_slippage_pct": 0.20,
        "quote_age_seconds": 2.5,
        "liquidity_score": 0.75,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }

    result = verify_route(payload)

    assert result.decision in ["BLOCK", "REVIEW"]
    assert result.metadata["policy_profile"] == "conservative"
    assert "minimum_profit_buffer" in result.failed_conditions
    assert "fresh_quote" in result.failed_conditions
    assert "liquidity_confidence" in result.failed_conditions


def test_usage_lookup_by_request_id():
    from usage_meter import log_usage_event, get_usage_event_by_request_id

    result = {
        "request_id": "lookup-test-request-id",
        "decision": "BLOCK",
        "safety_score": 0.25,
        "metadata": {
            "agent_id": "lookup-test-agent",
            "request_id": "lookup-test-request-id",
            "endpoint": "/test/lookup"
        }
    }

    log_usage_event("/test/lookup", result, api_key_label="test")
    event = get_usage_event_by_request_id("lookup-test-request-id")

    assert event is not None
    assert event["request_id"] == "lookup-test-request-id"
    assert event["decision"] == "BLOCK"
    assert event["agent_id"] == "lookup-test-agent"
