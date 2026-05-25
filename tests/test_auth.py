import pytest
import time
import jwt
from fastapi.testclient import TestClient
from src.api.server import create_app
from src.api.middleware import validate_bearer_token, JWT_SECRET, JWT_ISSUER, JWT_AUDIENCE
from src.common.errors import AuthenticationError


def create_token(sub="valid_user", jti="token123", expired=False, invalid_sig=False, 
                 issuer=JWT_ISSUER, audience=JWT_AUDIENCE):
    payload = {
        "sub": sub,
        "jti": jti,
        "iss": issuer,
        "aud": audience,
        "iat": int(time.time()),
        "exp": int(time.time()) + (3600 if not expired else -3600)
    }
    secret = JWT_SECRET if not invalid_sig else "wrong_secret"
    return jwt.encode(payload, secret, algorithm="HS256")


def test_validate_bearer_token_direct():
    valid_token = create_token(sub="valid_user")
    
    # Valid token
    assert validate_bearer_token(f"Bearer {valid_token}") == valid_token
    # Case-insensitive scheme
    assert validate_bearer_token(f"bearer {valid_token}") == valid_token
    assert validate_bearer_token(f"BEARER {valid_token}") == valid_token
    assert validate_bearer_token(f"BeArEr {valid_token}") == valid_token

    # Missing header
    with pytest.raises(AuthenticationError, match="Missing Authorization header"):
        validate_bearer_token("")

    # Invalid scheme
    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        validate_bearer_token(f"Basic {valid_token}")

    with pytest.raises(AuthenticationError, match="Invalid auth scheme"):
        validate_bearer_token("Bearer")
        
    # Invalid signature
    invalid_sig_token = create_token(invalid_sig=True)
    with pytest.raises(AuthenticationError, match="Invalid token signature"):
        validate_bearer_token(f"Bearer {invalid_sig_token}")

    # Stale, revoked, anonymous, insufficient scope
    stale_token = create_token(expired=True)
    with pytest.raises(AuthenticationError, match="Stale credentials"):
        validate_bearer_token(f"Bearer {stale_token}")

    revoked_token = create_token(jti="revoked_token_id")
    with pytest.raises(AuthenticationError, match="Revoked credentials"):
        validate_bearer_token(f"bearer {revoked_token}")

    anonymous_token = create_token(sub="anonymous")
    with pytest.raises(AuthenticationError, match="Anonymous principals denied"):
        validate_bearer_token(f"BEARER {anonymous_token}")

    insufficient_token = create_token(sub="insufficient_user")
    with pytest.raises(PermissionError, match="Insufficient scope"):
        validate_bearer_token(f"Bearer {insufficient_token}")

    # Workspace role checks
    # GET works for read/guest roles
    guest_token = create_token(sub="guest_user")
    assert validate_bearer_token(f"Bearer {guest_token}", "GET") == guest_token
    # Mutating actions fail for guest roles
    with pytest.raises(PermissionError, match="Insufficient workspace role"):
        validate_bearer_token(f"Bearer {guest_token}", "POST")


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
        token = create_token(sub="valid_user")
        headers = {"Authorization": f"Basic {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Invalid auth scheme" in response.text

    def test_valid_token_succeeds(self):
        token = create_token(sub="valid_user")
        headers = {"Authorization": f"bearer {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 200

    def test_stale_token_denied(self):
        token = create_token(expired=True)
        headers = {"Authorization": f"bearer {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Stale credentials" in response.text

    def test_revoked_token_denied(self):
        token = create_token(jti="revoked_token_id")
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Revoked credentials" in response.text

    def test_anonymous_token_denied(self):
        token = create_token(sub="anonymous")
        headers = {"Authorization": f"BEARER {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Anonymous principals denied" in response.text

    def test_insufficient_scope_denied(self):
        token = create_token(sub="insufficient_user")
        headers = {"Authorization": f"bearer {token}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 403
        assert "Insufficient scope" in response.text

    def test_guest_mutating_action_forbidden(self):
        token = create_token(sub="guest_user")
        path = "/api/v2/agents?name=test&agent_type=type"
        headers = {"Authorization": f"bearer {token}"}
        response = self.client.post(path, headers=headers)
        assert response.status_code == 403
        assert "Insufficient workspace role" in response.text
