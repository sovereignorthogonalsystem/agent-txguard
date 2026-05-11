from dataclasses import asdict
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from guard import verify_route, verify_simulation


app = FastAPI(
    title="AgentTxGuard",
    description="Preflight verification API for autonomous Solana agents.",
    version="0.1.0",
)


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


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "name": "AgentTxGuard",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "route_verification": "/verify/route",
        "simulation_verification": "/verify/simulation",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/verify/route")
def verify_route_endpoint(payload: RouteVerificationRequest) -> Dict[str, Any]:
    result = verify_route(payload.model_dump())
    return asdict(result)


@app.post("/verify/simulation")
def verify_simulation_endpoint(payload: SimulationVerificationRequest) -> Dict[str, Any]:
    result = verify_simulation(payload.model_dump())
    return asdict(result)
