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
