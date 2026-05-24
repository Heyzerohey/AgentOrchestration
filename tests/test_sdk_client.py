import os
import pytest
from src.sdk.client import OrchestratorClient


def test_client_init_success():
    client = OrchestratorClient(api_key="valid-key")
    assert client.api_key == "valid-key"


def test_client_init_env_var(monkeypatch):
    monkeypatch.setenv("AO_API_KEY", "env-key")
    client = OrchestratorClient()
    assert client.api_key == "env-key"


def test_client_init_missing_raises_value_error(monkeypatch):
    monkeypatch.delenv("AO_API_KEY", raising=False)
    with pytest.raises(ValueError) as exc:
        OrchestratorClient()
    assert "API key is missing or empty" in str(exc.value)


def test_client_init_whitespace_raises_value_error(monkeypatch):
    monkeypatch.setenv("AO_API_KEY", "   ")
    with pytest.raises(ValueError) as exc:
        OrchestratorClient()
    assert "API key is missing or empty" in str(exc.value)
