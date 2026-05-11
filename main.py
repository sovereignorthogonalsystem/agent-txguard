from dataclasses import asdict
from typing import Any, Dict, Optional
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from rpc_simulator import simulate_transaction
from usage_meter import log_usage_event, usage_summary

from guard import verify_route, verify_simulation, verify_rpc_simulation_result, verify_jupiter_quote


app = FastAPI(
    title="AgentTxGuard",
    description="Preflight verification API for autonomous Solana agents.",
    version="0.1.0",
)


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    expected_key = os.getenv("AGENTTXGUARD_API_KEY")

    # If no API key is configured, allow local/dev usage.
    if not expected_key:
        return

    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")



class RouteVerificationRequest(BaseModel):
    agent_id: str = Field(default="demo-agent")
    chain: str = Field(default="solana")
    intent: str = Field(default="swap")

    input_mint: Optional[str] = None
    output_mint: Optional[str] = None

    nominal_profit_pct: float = 0.0
    estimated_fees_pct: float = 0.0
    estimated_slippage_pct: float = 0.0
    quote_age_seconds: float = 999.0
    liquidity_score: float = 0.0

    minimum_profit_pct: float = 0.25
    max_quote_age_seconds: float = 3.0
    minimum_liquidity_score: float = 0.70
    max_slippage_pct: float = 0.50

    private_key_supplied: bool = False
    seed_phrase_supplied: bool = False


class SimulationVerificationRequest(BaseModel):
    agent_id: str = Field(default="demo-agent")
    chain: str = Field(default="solana")
    intent: str = Field(default="transaction")

    simulation_ok: bool = False
    simulation_error: Optional[str] = None

    wallet_delta_lamports: int = 0

    compute_units_used: int = 0
    max_compute_units: int = 200000

    priority_fee_lamports: int = 0
    max_priority_fee_lamports: int = 10000

    blockhash_age_slots: int = 999999
    max_blockhash_age_slots: int = 120

    private_key_supplied: bool = False
    seed_phrase_supplied: bool = False


class SolanaRpcSimulationRequest(BaseModel):
    agent_id: str = Field(default="demo-agent")
    chain: str = Field(default="solana")

    transaction_base64: str
    rpc_url: str = Field(default="https://api.mainnet-beta.solana.com")

    commitment: str = Field(default="confirmed")
    replace_recent_blockhash: bool = True
    sig_verify: bool = False

    max_compute_units: int = 200000
    max_fee_lamports: int = 10000


class JupiterQuoteVerificationRequest(BaseModel):
    agent_id: str = Field(default="demo-agent")
    chain: str = Field(default="solana")

    quote: Dict[str, Any]

    current_slot: Optional[int] = None

    max_slippage_bps: int = 50
    max_price_impact_pct: float = 0.50
    max_time_taken: float = 0.50
    max_slot_lag: int = 150


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "name": "AgentTxGuard",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "route_verification": "/verify/route",
        "simulation_verification": "/verify/simulation",
        "solana_rpc_simulation": "/verify/solana-rpc-simulation",
        "jupiter_quote_verification": "/verify/jupiter-quote",
        "usage_summary": "/usage/summary",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/verify/route")
def verify_route_endpoint(payload: RouteVerificationRequest, _: None = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
    require_api_key(_)
    result = verify_route(payload.model_dump())
    response = asdict(result)
    log_usage_event("/verify/route", response, api_key_label="configured" if os.getenv("AGENTTXGUARD_API_KEY") else "local-dev")
    return response


@app.post("/verify/simulation")
def verify_simulation_endpoint(payload: SimulationVerificationRequest, _: None = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
    require_api_key(_)
    result = verify_simulation(payload.model_dump())
    response = asdict(result)
    log_usage_event("/verify/simulation", response, api_key_label="configured" if os.getenv("AGENTTXGUARD_API_KEY") else "local-dev")
    return response


@app.post("/verify/solana-rpc-simulation")
def verify_solana_rpc_simulation_endpoint(payload: SolanaRpcSimulationRequest, _: None = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
    require_api_key(_)
    try:
        sim = simulate_transaction(
            transaction_base64=payload.transaction_base64,
            rpc_url=payload.rpc_url,
            commitment=payload.commitment,
            replace_recent_blockhash=payload.replace_recent_blockhash,
            sig_verify=payload.sig_verify,
        )

        evaluation_payload = {
            "agent_id": payload.agent_id,
            "rpc_url": payload.rpc_url,
            "rpc_ok": True,
            "rpc_error": None,
            "slot": sim.get("slot"),
            "value": sim.get("value"),
            "max_compute_units": payload.max_compute_units,
            "max_fee_lamports": payload.max_fee_lamports,
        }

    except Exception as exc:
        evaluation_payload = {
            "agent_id": payload.agent_id,
            "rpc_url": payload.rpc_url,
            "rpc_ok": False,
            "rpc_error": str(exc),
            "value": {},
            "max_compute_units": payload.max_compute_units,
            "max_fee_lamports": payload.max_fee_lamports,
        }

    result = verify_rpc_simulation_result(evaluation_payload)
    response = asdict(result)
    log_usage_event("/verify/solana-rpc-simulation", response, api_key_label="configured" if os.getenv("AGENTTXGUARD_API_KEY") else "local-dev")
    return response


@app.post("/verify/jupiter-quote")
def verify_jupiter_quote_endpoint(payload: JupiterQuoteVerificationRequest, _: None = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
    require_api_key(_)
    result = verify_jupiter_quote(payload.model_dump())
    response = asdict(result)
    log_usage_event("/verify/jupiter-quote", response, api_key_label="configured" if os.getenv("AGENTTXGUARD_API_KEY") else "local-dev")
    return response


@app.get("/usage/summary")
def usage_summary_endpoint(_: Optional[str] = Header(default=None, alias="X-API-Key")) -> Dict[str, Any]:
    require_api_key(_)
    return usage_summary()
