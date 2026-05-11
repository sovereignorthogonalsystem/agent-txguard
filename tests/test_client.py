import pytest

from client import AgentTxGuardClient


def test_client_builds_headers_without_api_key():
    client = AgentTxGuardClient()
    headers = client._headers()

    assert headers["Content-Type"] == "application/json"
    assert "X-API-Key" not in headers


def test_client_builds_headers_with_api_key():
    client = AgentTxGuardClient(api_key="test-key")
    headers = client._headers()

    assert headers["Content-Type"] == "application/json"
    assert headers["X-API-Key"] == "test-key"


def test_client_base_url_strips_trailing_slash():
    client = AgentTxGuardClient(base_url="http://127.0.0.1:8000/")

    assert client.base_url == "http://127.0.0.1:8000"


def test_client_methods_exist():
    client = AgentTxGuardClient()

    assert callable(client.health)
    assert callable(client.verify_route)
    assert callable(client.verify_simulation)
    assert callable(client.verify_jupiter_quote)
    assert callable(client.verify_solana_rpc_simulation)
    assert callable(client.usage_summary)
    assert callable(client.usage_policy)
    assert callable(client.audit_request)
    assert callable(client.policies)
