import os
import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app


def test_cors_options_preflight_bypass(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.agent-orchestrator.io")
    app = create_app()
    client = TestClient(app)

    # OPTIONS preflight request from allowed origin
    headers = {
        "Origin": "https://app.agent-orchestrator.io",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization",
    }
    response = client.options("/api/v2/agents", headers=headers)
    # The preflight OPTIONS request is handled by CORSMiddleware and bypasses AuthMiddleware
    assert response.status_code == 200


def test_cors_credentialed_request_allowed_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.agent-orchestrator.io,https://another-trusted.io")
    app = create_app()
    client = TestClient(app)

    # Valid credentialed request from allowed origin
    headers = {
        "Origin": "https://app.agent-orchestrator.io",
        "Authorization": "Bearer test-token",
    }
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 200


def test_cors_credentialed_request_forbidden_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.agent-orchestrator.io")
    app = create_app()
    client = TestClient(app)

    # Credentialed request from untrusted origin -> 403 Forbidden
    headers = {
        "Origin": "https://malicious.com",
        "Authorization": "Bearer test-token",
    }
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 403
    assert response.text == "Origin not allowed"


def test_cors_credentialed_request_unsafe_wildcard(monkeypatch):
    # Wildcard CORS origins are unsafe for credentialed requests
    monkeypatch.setenv("CORS_ORIGINS", "*")
    app = create_app()
    client = TestClient(app)

    headers = {
        "Origin": "https://app.agent-orchestrator.io",
        "Authorization": "Bearer test-token",
    }
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 400
    assert "Unsafe CORS configuration for credentialed requests" in response.text


def test_cors_non_credentialed_request_wildcard(monkeypatch):
    # Non-credentialed requests (like health checks) can safely pass even with wildcard
    monkeypatch.setenv("CORS_ORIGINS", "*")
    app = create_app()
    client = TestClient(app)

    headers = {
        "Origin": "https://any-origin.io",
    }
    response = client.get("/health", headers=headers)
    assert response.status_code == 200
