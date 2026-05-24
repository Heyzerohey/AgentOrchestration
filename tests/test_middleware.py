"""Integration regression tests for PathMiddleware."""

import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app


def test_path_middleware_collapsing_slashes_client():
    app = create_app()
    client = TestClient(app)

    # 1. Test normal public health route
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

    # 2. Test private route with inner duplicate slashes
    response = client.get("/api/v2//agents")
    assert response.status_code == 401

    # 3. Test private route with valid token
    response = client.get("/api/v2/agents", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200

    # 4. Test public endpoint with duplicate slashes
    response = client.post("/api/v2//auth/token")
    assert response.status_code == 404  # Not 401 Unauthorized


@pytest.mark.anyio
async def test_path_middleware_direct_asgi():
    app = create_app()

    # Verify that a leading double slash is correctly collapsed in the scope
    # and properly intercepted by AuthMiddleware yielding a 401.
    scope = {
        "type": "http",
        "method": "GET",
        "path": "//api/v2/agents",
        "raw_path": b"//api/v2/agents",
        "headers": [],
    }

    async def receive():
        return {"type": "http.request"}

    sent_messages = []
    async def send(message):
        sent_messages.append(message)

    await app(scope, receive, send)

    # Assert that the scope itself was mutated and collapsed correctly
    assert scope["path"] == "/api/v2/agents"
    assert scope["raw_path"] == b"/api/v2/agents"

    # Assert that it correctly resulted in a 401 Unauthorized response from AuthMiddleware
    start_message = next(msg for msg in sent_messages if msg["type"] == "http.response.start")
    assert start_message["status"] == 401
