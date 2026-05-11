#!/usr/bin/env bash

set -e

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo ""
echo "AgentTxGuard demo"
echo "Base URL: $BASE_URL"
echo ""

echo "1. Health check"
curl -s "$BASE_URL/health"
echo ""
echo ""

echo "2. Route preflight — expected BLOCK"
curl -s -X POST "$BASE_URL/verify/route" \
  -H "Content-Type: application/json" \
  -d @examples/proposed_swap_block.json
echo ""
echo ""

echo "3. Route preflight — expected PASS"
curl -s -X POST "$BASE_URL/verify/route" \
  -H "Content-Type: application/json" \
  -d @examples/proposed_swap_pass.json
echo ""
echo ""

echo "4. Simulation preflight — expected BLOCK"
curl -s -X POST "$BASE_URL/verify/simulation" \
  -H "Content-Type: application/json" \
  -d @examples/simulation_block.json
echo ""
echo ""

echo "5. Simulation preflight — expected PASS"
curl -s -X POST "$BASE_URL/verify/simulation" \
  -H "Content-Type: application/json" \
  -d @examples/simulation_pass.json
echo ""
echo ""
