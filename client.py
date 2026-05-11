from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class AgentTxGuardClient:
    """
    Lightweight Python client for AgentTxGuard.

    This client does not sign transactions, hold funds, or manage private keys.
    It only calls a running AgentTxGuard API.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        api_key: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        return headers

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, json=payload, headers=self._headers())

        response.raise_for_status()
        return response.json()

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(url, headers=self._headers())

        response.raise_for_status()
        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def verify_route(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/verify/route", payload)

    def verify_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/verify/simulation", payload)

    def verify_jupiter_quote(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/verify/jupiter-quote", payload)

    def verify_solana_rpc_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/verify/solana-rpc-simulation", payload)

    def usage_summary(self) -> Dict[str, Any]:
        return self._get("/usage/summary")

    def usage_policy(self) -> Dict[str, Any]:
        return self._get("/usage/policy")

    def audit_request(self, request_id: str) -> Dict[str, Any]:
        return self._get(f"/audit/request/{request_id}")

    def policies(self) -> Dict[str, Any]:
        return self._get("/policies")
