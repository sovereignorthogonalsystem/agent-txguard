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
