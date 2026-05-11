from __future__ import annotations

from typing import Any, Dict

import httpx


DEFAULT_SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"


class SolanaRpcSimulationError(RuntimeError):
    pass


def simulate_transaction(
    transaction_base64: str,
    rpc_url: str = DEFAULT_SOLANA_RPC_URL,
    commitment: str = "confirmed",
    replace_recent_blockhash: bool = True,
    sig_verify: bool = False,
    timeout_seconds: float = 10.0,
) -> Dict[str, Any]:
    """
    Call Solana simulateTransaction.

    The transaction is not broadcast.
    No private key or seed phrase is accepted.
    """

    if not transaction_base64 or not isinstance(transaction_base64, str):
        raise ValueError("transaction_base64 must be a non-empty base64 string.")

    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "simulateTransaction",
        "params": [
            transaction_base64,
            {
                "encoding": "base64",
                "commitment": commitment,
                "replaceRecentBlockhash": replace_recent_blockhash,
                "sigVerify": sig_verify,
            },
        ],
    }

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(rpc_url, json=body)

    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise SolanaRpcSimulationError(str(data["error"]))

    result = data.get("result") or {}
    context = result.get("context") or {}
    value = result.get("value") or {}

    return {
        "slot": context.get("slot"),
        "value": value,
        "raw": data,
    }
