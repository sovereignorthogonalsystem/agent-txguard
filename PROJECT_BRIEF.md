# AgentTxGuard: Preflight Verification Middleware for Autonomous Solana Agents

## Summary

AgentTxGuard is a non-custodial preflight verification API for autonomous Solana agents.

It checks proposed routes, Jupiter quotes, simulation reports, and Solana RPC simulateTransaction results before an agent signs or broadcasts a transaction.

## Problem

Autonomous crypto agents can generate transactions faster than humans can inspect them.

That creates risks such as stale quotes, unsafe slippage, weak liquidity, negative net return, failed simulations, excessive compute usage, excessive fees, stale blockhashes, suspicious logs, and missing audit trails.

## Solution

AgentTxGuard acts as a pre-execution safety layer.

It does not hold funds, custody assets, accept private keys, accept seed phrases, sign transactions, or broadcast transactions.

It evaluates proposed actions and returns PASS, BLOCK, or REVIEW with a safety score, failed conditions, failure report, request ID, endpoint metadata, and audit trail.

## Current API Endpoints

Public:

- GET /
- GET /health
- GET /policies

Verification:

- POST /verify/route
- POST /verify/simulation
- POST /verify/solana-rpc-simulation
- POST /verify/jupiter-quote

Usage and audit:

- GET /usage/summary
- GET /usage/policy
- GET /audit/request/{request_id}

## Core Features

- Route metadata preflight
- Simulation-result preflight
- Solana RPC simulateTransaction verification
- Jupiter quote verification
- Risk policy profiles
- API key authentication
- Usage metering
- Quota policy and enforcement
- Request IDs
- Audit lookup by request ID
- Python client SDK

## Risk Policy Profiles

Supported profiles:

- conservative
- balanced
- aggressive

Profiles tune thresholds for minimum profit, quote freshness, liquidity confidence, slippage, price impact, slot freshness, compute units, and fees.

## Python Client SDK

AgentTxGuard includes a lightweight Python client for bots and agent pipelines.

Example:

from client import AgentTxGuardClient

client = AgentTxGuardClient(base_url="http://127.0.0.1:8000")
result = client.verify_route({...})
print(result["decision"])
print(result["request_id"])

## Example Use Cases

- autonomous Solana trading agents
- AI-generated swap execution workflows
- Jupiter route preflight checks
- bot risk filters
- transaction simulation gates
- wallet/action safety middleware
- internal audit logs for agent decisions
- hosted verification API for crypto automation teams

## Why It Matters

Autonomous agents need guardrails before execution.

A bot can be fast and still be wrong.

AgentTxGuard provides a preflight layer between agent proposal and transaction signing or broadcasting.

## Status

Experimental MVP.

AgentTxGuard is not financial, legal, security, investment, or professional advice.

Never send private keys, seed phrases, or wallet secrets to this service.
