import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app
from src.api.middleware import validate_bearer_token
from src.common.errors import AuthenticationError


def test_validate_bearer_token_direct():
    # Valid token
    assert validate_bearer_token("Bearer valid_token") == "valid_token"
    # Case-insensitive scheme
    assert validate_bearer_token("bearer token123") == "token123"
    assert validate_bearer_token("BEARER admin_token") == "admin_token"
    assert validate_bearer_token("BeArEr custom_token") == "custom_token"

    # Missing header
    with pytest.raises(
        AuthenticationError, match="Missing Authorization header"
    ):
        validate_bearer_token("")

    # Invalid scheme
    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        validate_bearer_token("Basic abc")

    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        validate_bearer_token("Bearer")

    # Stale, revoked, anonymous, insufficient scope
    with pytest.raises(AuthenticationError, match="Stale credentials"):
        validate_bearer_token("Bearer stale_token")

    with pytest.raises(AuthenticationError, match="Revoked credentials"):
        validate_bearer_token("bearer revoked_session")

    with pytest.raises(
        AuthenticationError, match="Anonymous principals denied"
    ):
        validate_bearer_token("BEARER anonymous_user")

    with pytest.raises(PermissionError, match="Insufficient scope"):
        validate_bearer_token("Bearer insufficient_scope")

    # Workspace role checks
    # GET works for read/guest roles
    assert validate_bearer_token("Bearer guest_user", "GET") == "guest_user"
    # Mutating actions fail for guest roles
    with pytest.raises(PermissionError, match="Insufficient workspace role"):
        validate_bearer_token("Bearer guest_user", "POST")


class TestAuthIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_unauthenticated_request_fails(self):
        response = self.client.get("/api/v2/agents")
        assert response.status_code == 401
        assert "Missing Authorization header" in response.text

    def test_invalid_scheme_fails(self):
        headers = {"Authorization": "Basic user:pass"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Invalid auth scheme" in response.text

    def test_valid_token_succeeds(self):
        headers = {"Authorization": "bearer valid_user"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 200

    def test_stale_token_denied(self):
        headers = {"Authorization": "bearer stale_session"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Stale credentials" in response.text

    def test_revoked_token_denied(self):
        headers = {"Authorization": "Bearer revoked_token"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Revoked credentials" in response.text

    def test_anonymous_token_denied(self):
        headers = {"Authorization": "BEARER anonymous_token"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Anonymous principals denied" in response.text

    def test_insufficient_scope_denied(self):
        headers = {"Authorization": "bearer insufficient_scope"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 403
        assert "Insufficient scope" in response.text

    def test_guest_mutating_action_forbidden(self):
        path = "/api/v2/agents?name=test&agent_type=type"
        headers = {"Authorization": "bearer guest_token"}
        response = self.client.post(path, headers=headers)
        assert response.status_code == 403
        assert "Insufficient workspace role" in response.text
