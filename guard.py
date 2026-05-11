from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class GuardCondition:
    name: str
    passed: bool
    detail: str
    weight: float = 1.0
    severity: str = "medium"


@dataclass
class GuardResult:
    decision: str
    safety_score: float
    passed_conditions: List[str] = field(default_factory=list)
    failed_conditions: List[str] = field(default_factory=list)
    failure_report: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentTxGuard:
    def __init__(self, pass_threshold: float = 0.85, review_threshold: float = 0.60):
        if not 0 <= review_threshold <= pass_threshold <= 1:
            raise ValueError("Thresholds must satisfy 0 <= review <= pass <= 1.")
        self.pass_threshold = pass_threshold
        self.review_threshold = review_threshold

    def evaluate(self, conditions: List[GuardCondition], metadata: Dict[str, Any]) -> GuardResult:
        if not conditions:
            return GuardResult(
                decision="REVIEW",
                safety_score=0.0,
                failure_report=["No preflight conditions supplied."],
                metadata=metadata,
            )

        total_weight = sum(max(c.weight, 0.0) for c in conditions)
        if total_weight == 0:
            return GuardResult(
                decision="REVIEW",
                safety_score=0.0,
                failure_report=["All preflight condition weights are zero."],
                metadata=metadata,
            )

        passed_weight = sum(c.weight for c in conditions if c.passed and c.weight > 0)
        safety_score = passed_weight / total_weight

        passed = [c.name for c in conditions if c.passed]
        failed = [c.name for c in conditions if not c.passed]

        failure_report = [
            f"[{c.severity.upper()}] {c.name}: {c.detail}"
            for c in conditions
            if not c.passed
        ]

        critical_failed = any(
            (not c.passed) and c.severity.lower() == "critical"
            for c in conditions
        )

        if critical_failed:
            decision = "BLOCK"
        elif safety_score >= self.pass_threshold and not failed:
            decision = "PASS"
        elif safety_score >= self.review_threshold:
            decision = "REVIEW"
        else:
            decision = "BLOCK"

        return GuardResult(
            decision=decision,
            safety_score=round(safety_score, 4),
            passed_conditions=passed,
            failed_conditions=failed,
            failure_report=failure_report,
            metadata=metadata,
        )


def verify_route(payload: Dict[str, Any]) -> GuardResult:
    chain = str(payload.get("chain", "solana")).lower()

    nominal_profit_pct = float(payload.get("nominal_profit_pct", 0.0))
    estimated_fees_pct = float(payload.get("estimated_fees_pct", 0.0))
    estimated_slippage_pct = float(payload.get("estimated_slippage_pct", 0.0))
    quote_age_seconds = float(payload.get("quote_age_seconds", 999.0))
    liquidity_score = float(payload.get("liquidity_score", 0.0))

    minimum_profit_pct = float(payload.get("minimum_profit_pct", 0.25))
    max_quote_age_seconds = float(payload.get("max_quote_age_seconds", 3.0))
    minimum_liquidity_score = float(payload.get("minimum_liquidity_score", 0.70))
    max_slippage_pct = float(payload.get("max_slippage_pct", 0.50))

    private_key_supplied = bool(payload.get("private_key_supplied", False))
    seed_phrase_supplied = bool(payload.get("seed_phrase_supplied", False))

    net_profit_pct = nominal_profit_pct - estimated_fees_pct - estimated_slippage_pct

    conditions = [
        GuardCondition(
            name="non_custodial_request",
            passed=not private_key_supplied and not seed_phrase_supplied,
            detail="Private keys or seed phrases must never be supplied to AgentTxGuard.",
            weight=5.0,
            severity="critical",
        ),
        GuardCondition(
            name="supported_chain",
            passed=chain == "solana",
            detail=f"Unsupported chain: {chain}. MVP supports Solana only.",
            weight=2.0,
            severity="critical",
        ),
        GuardCondition(
            name="positive_net_return",
            passed=net_profit_pct > 0,
            detail=f"Net return after fees and slippage is {net_profit_pct:.4f}%.",
            weight=3.0,
            severity="critical",
        ),
        GuardCondition(
            name="minimum_profit_buffer",
            passed=net_profit_pct >= minimum_profit_pct,
            detail=f"Net return {net_profit_pct:.4f}% is below required buffer {minimum_profit_pct:.4f}%.",
            weight=2.0,
            severity="high",
        ),
        GuardCondition(
            name="fresh_quote",
            passed=quote_age_seconds <= max_quote_age_seconds,
            detail=f"Quote age is {quote_age_seconds:.2f}s; maximum allowed is {max_quote_age_seconds:.2f}s.",
            weight=1.5,
            severity="high",
        ),
        GuardCondition(
            name="liquidity_confidence",
            passed=liquidity_score >= minimum_liquidity_score,
            detail=f"Liquidity score is {liquidity_score:.2f}; minimum required is {minimum_liquidity_score:.2f}.",
            weight=1.5,
            severity="medium",
        ),
        GuardCondition(
            name="slippage_ceiling",
            passed=estimated_slippage_pct <= max_slippage_pct,
            detail=f"Estimated slippage is {estimated_slippage_pct:.4f}%; maximum allowed is {max_slippage_pct:.4f}%.",
            weight=1.5,
            severity="high",
        ),
    ]

    guard = AgentTxGuard()

    return guard.evaluate(
        conditions,
        metadata={
            "agent_id": payload.get("agent_id"),
            "chain": chain,
            "intent": payload.get("intent", "unknown"),
            "input_mint": payload.get("input_mint"),
            "output_mint": payload.get("output_mint"),
            "nominal_profit_pct": nominal_profit_pct,
            "estimated_fees_pct": estimated_fees_pct,
            "estimated_slippage_pct": estimated_slippage_pct,
            "net_profit_pct": round(net_profit_pct, 4),
            "quote_age_seconds": quote_age_seconds,
            "liquidity_score": liquidity_score,
        },
    )


def verify_simulation(payload: Dict[str, Any]) -> GuardResult:
    """
    Verify a transaction simulation result before an autonomous agent signs or broadcasts.

    This MVP does not call Solana RPC directly.
    It evaluates simulation-like fields supplied by the caller.

    Checks:
    - non-custodial safety
    - simulation success
    - wallet-level positive balance delta
    - compute unit ceiling
    - priority fee ceiling
    - stale blockhash risk
    """

    simulation_ok = bool(payload.get("simulation_ok", False))
    simulation_error = payload.get("simulation_error")

    wallet_delta_lamports = int(payload.get("wallet_delta_lamports", 0))
    compute_units_used = int(payload.get("compute_units_used", 0))
    max_compute_units = int(payload.get("max_compute_units", 200000))

    priority_fee_lamports = int(payload.get("priority_fee_lamports", 0))
    max_priority_fee_lamports = int(payload.get("max_priority_fee_lamports", 10000))

    blockhash_age_slots = int(payload.get("blockhash_age_slots", 999999))
    max_blockhash_age_slots = int(payload.get("max_blockhash_age_slots", 120))

    private_key_supplied = bool(payload.get("private_key_supplied", False))
    seed_phrase_supplied = bool(payload.get("seed_phrase_supplied", False))

    conditions = [
        GuardCondition(
            name="non_custodial_request",
            passed=not private_key_supplied and not seed_phrase_supplied,
            detail="Private keys or seed phrases must never be supplied to AgentTxGuard.",
            weight=5.0,
            severity="critical",
        ),
        GuardCondition(
            name="simulation_success",
            passed=simulation_ok and not simulation_error,
            detail=f"Simulation failed or returned error: {simulation_error}",
            weight=5.0,
            severity="critical",
        ),
        GuardCondition(
            name="positive_wallet_delta",
            passed=wallet_delta_lamports > 0,
            detail=f"Wallet delta is {wallet_delta_lamports} lamports.",
            weight=3.0,
            severity="critical",
        ),
        GuardCondition(
            name="compute_unit_ceiling",
            passed=compute_units_used <= max_compute_units,
            detail=(
                f"Compute units used {compute_units_used}; maximum allowed is "
                f"{max_compute_units}."
            ),
            weight=2.0,
            severity="high",
        ),
        GuardCondition(
            name="priority_fee_ceiling",
            passed=priority_fee_lamports <= max_priority_fee_lamports,
            detail=(
                f"Priority fee {priority_fee_lamports} lamports; maximum allowed is "
                f"{max_priority_fee_lamports}."
            ),
            weight=1.5,
            severity="medium",
        ),
        GuardCondition(
            name="fresh_blockhash",
            passed=blockhash_age_slots <= max_blockhash_age_slots,
            detail=(
                f"Blockhash age is {blockhash_age_slots} slots; maximum allowed is "
                f"{max_blockhash_age_slots}."
            ),
            weight=2.0,
            severity="high",
        ),
    ]

    guard = AgentTxGuard()

    return guard.evaluate(
        conditions,
        metadata={
            "agent_id": payload.get("agent_id"),
            "chain": payload.get("chain", "solana"),
            "intent": payload.get("intent", "transaction"),
            "simulation_ok": simulation_ok,
            "simulation_error": simulation_error,
            "wallet_delta_lamports": wallet_delta_lamports,
            "compute_units_used": compute_units_used,
            "priority_fee_lamports": priority_fee_lamports,
            "blockhash_age_slots": blockhash_age_slots,
        },
    )
