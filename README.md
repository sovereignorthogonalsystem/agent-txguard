# AgentTxGuard

AgentTxGuard is a preflight verification API for autonomous Solana agents.

It checks proposed swaps and transactions before execution and returns PASS, BLOCK, or REVIEW with a safety score and failure report.

## What It Does

- Does not trade
- Does not custody funds
- Does not sign transactions
- Does not accept private keys or seed phrases
- Checks proposed agent actions before execution

## Current MVP

- Non-custodial safety
- Positive net return
- Minimum profit buffer
- Quote freshness
- Liquidity confidence
- Slippage ceiling
- Solana-only chain allowlist

## Endpoints

- GET /
- GET /health
- POST /verify/route

## Run Locally

pip install -r requirements.txt
uvicorn main:app --reload

Open:

http://127.0.0.1:8000/docs

## Test

pytest

## Status

Experimental prototype. Not financial, legal, security, investment, or professional advice.

Never send private keys, seed phrases, or wallet secrets to this service.

## Simulation Verification

AgentTxGuard also supports simulation-style transaction preflight:

- simulation success/failure
- wallet-level balance delta
- compute unit ceiling
- priority fee ceiling
- blockhash freshness

Endpoint:

- POST /verify/simulation

Example:

curl -X POST "http://127.0.0.1:8000/verify/simulation" \
  -H "Content-Type: application/json" \
  -d @examples/simulation_block.json

## Real Solana RPC Simulation

AgentTxGuard includes a Solana RPC simulation endpoint:

- POST /verify/solana-rpc-simulation

It accepts a base64-encoded transaction, calls Solana simulateTransaction, and evaluates:

- RPC call success
- simulation error
- compute units consumed
- fee ceiling
- suspicious simulation logs

This endpoint does not broadcast transactions and never accepts private keys or seed phrases.

## Jupiter Quote Verification

AgentTxGuard includes a Jupiter quote preflight endpoint:

- POST /verify/jupiter-quote

It evaluates Jupiter quote fields including:

- outAmount
- otherAmountThreshold
- slippageBps
- priceImpactPct
- routePlan
- contextSlot freshness
- timeTaken latency

This helps autonomous agents block stale, high-impact, high-slippage, or invalid routes before building a swap transaction.

## Docker

Build and run:

```bash
docker build -t agent-txguard .
docker run -p 8000:8000 agent-txguard
```

Or with Docker Compose:

```bash
docker compose up --build
```

## Deploy

This repo includes a `render.yaml` for simple Render deployment.

## API Key Authentication

For hosted deployments, set:

```bash
AGENTTXGUARD_API_KEY=your-secret-key
```

Then call protected endpoints with:

```bash
curl -X POST "http://127.0.0.1:8000/verify/route" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d @examples/proposed_swap_pass.json
```

If `AGENTTXGUARD_API_KEY` is unset, the API allows local development without a key.

## Usage Metering

AgentTxGuard includes local SQLite usage metering for hosted API development.

Usage events track:

- endpoint
- decision
- safety score
- agent ID
- timestamp

Endpoint:

- GET /usage/summary

The SQLite database is ignored by Git and is intended for local/dev usage. For production, replace it with Postgres, Supabase, or another managed database.

## Usage Plans

AgentTxGuard includes a simple usage-plan policy layer for hosted API development.

Default plan:

- free: 1,000 calls/month

Other supported plans:

- starter: 10,000 calls/month
- pro: 100,000 calls/month
- enterprise: custom/unlimited

Set the active plan with:

```bash
AGENTTXGUARD_PLAN=starter
```

Endpoint:

- GET /usage/policy

## Quota Enforcement

Verification endpoints enforce the active monthly usage plan.

When usage exceeds the configured plan limit, protected verification endpoints return:

```text
429 Too Many Requests
```

Plan limits are reported at:

- GET /usage/policy

## Request IDs and Audit Trail

Every verification response includes:

- request_id
- endpoint

Usage logs also store request IDs, making it easier to trace why a route or transaction was passed, blocked, or sent to review.

## Risk Policy Profiles

AgentTxGuard supports configurable policy profiles:

- conservative
- balanced
- aggressive

Policy profiles tune thresholds for:

- minimum profit
- quote freshness
- liquidity confidence
- slippage
- price impact
- slot freshness
- compute units
- fees

Endpoint:

- GET /policies

Example request field:

```json
{ "policy_profile": "conservative" }
```

## Request Audit Lookup

AgentTxGuard can look up a stored audit event by request ID.

Endpoint:

- GET /audit/request/{request_id}

This helps clients trace why a route, quote, or transaction simulation was passed, blocked, or sent to review.

## Python Client SDK

AgentTxGuard includes a lightweight Python client:

```python
from client import AgentTxGuardClient

client = AgentTxGuardClient(base_url="http://127.0.0.1:8000")
result = client.verify_route({...})
print(result["decision"])
```

Run the demo:

```bash
uvicorn main:app --reload
python examples/client_demo.py
```

## Project Brief

See PROJECT_BRIEF.md for a product overview of AgentTxGuard, including the problem, solution, API endpoints, core features, and target use cases.
