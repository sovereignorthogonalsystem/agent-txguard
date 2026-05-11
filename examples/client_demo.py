from __future__ import annotations

from client import AgentTxGuardClient


def main() -> None:
    client = AgentTxGuardClient(base_url="http://127.0.0.1:8000")

    route_payload = {
        "agent_id": "client-demo-agent",
        "chain": "solana",
        "policy_profile": "balanced",
        "intent": "swap",
        "input_mint": "USDC",
        "output_mint": "SOL",
        "nominal_profit_pct": 1.2,
        "estimated_fees_pct": 0.12,
        "estimated_slippage_pct": 0.18,
        "quote_age_seconds": 1.1,
        "liquidity_score": 0.91,
        "private_key_supplied": False,
        "seed_phrase_supplied": False,
    }

    result = client.verify_route(route_payload)

    print("Decision:", result["decision"])
    print("Safety score:", result["safety_score"])
    print("Request ID:", result["request_id"])

    audit = client.audit_request(result["request_id"])
    print("Audit lookup:", audit)


if __name__ == "__main__":
    main()
