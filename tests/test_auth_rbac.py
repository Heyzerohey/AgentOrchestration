"""Integration regression tests for token RBAC permission separation."""

import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app


def test_rbac_user_admin_tokens():
    app = create_app()
    client = TestClient(app)

    # 1. User token should have full access
    headers = {"Authorization": "bearer user-admin-token"}
    
    # GET works
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 200

    # POST works (register agent)
    response = client.post("/api/v2/agents?name=agent1&agent_type=python", headers=headers)
    assert response.status_code == 200
    agent_id = response.json()["agent_id"]

    # DELETE works
    response = client.delete(f"/api/v2/agents/{agent_id}", headers=headers)
    assert response.status_code == 200


def test_rbac_machine_tokens():
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer machine-token"}

    # GET works
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 200

    # POST works
    response = client.post("/api/v2/agents?name=agent2&agent_type=python", headers=headers)
    assert response.status_code == 200
    agent_id = response.json()["agent_id"]

    # DELETE fails for machine token with 403 Forbidden
    response = client.delete(f"/api/v2/agents/{agent_id}", headers=headers)
    assert response.status_code == 403
    assert response.text == "Forbidden"


def test_rbac_guest_read_tokens():
    app = create_app()
    client = TestClient(app)

    headers = {"Authorization": "Bearer guest-read-token"}

    # GET works
    response = client.get("/api/v2/agents", headers=headers)
    assert response.status_code == 200

    # POST fails with 403 Forbidden
    response = client.post("/api/v2/agents?name=agent3&agent_type=python", headers=headers)
    assert response.status_code == 403

    # DELETE fails with 403 Forbidden
    response = client.delete("/api/v2/agents/some-id", headers=headers)
    assert response.status_code == 403


def test_rbac_stale_revoked_anonymous_tokens():
    app = create_app()
    client = TestClient(app)

    # Stale token
    response = client.get("/api/v2/agents", headers={"Authorization": "Bearer stale-token"})
    assert response.status_code == 401

    # Revoked token
    response = client.get("/api/v2/agents", headers={"Authorization": "Bearer token-revoked"})
    assert response.status_code == 401

    # Anonymous token
    response = client.get("/api/v2/agents", headers={"Authorization": "bearer anonymous"})
    assert response.status_code == 401

    # Invalid / default token
    response = client.get("/api/v2/agents", headers={"Authorization": "Bearer unknown-token"})
    assert response.status_code == 401


def test_rbac_casing_insensitivity():
    app = create_app()
    client = TestClient(app)

    # BEARER token casing check
    response = client.get("/api/v2/agents", headers={"Authorization": "BEARER user-token"})
    assert response.status_code == 200

    response = client.get("/api/v2/agents", headers={"Authorization": "bearer user-token"})
    assert response.status_code == 200
