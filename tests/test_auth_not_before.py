import time
import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app
from src.api.middleware import validate_bearer_token
from src.common.errors import AuthenticationError


def test_validate_bearer_token_not_before_active():
    # Past timestamp nbf should be active and valid
    past_timestamp = int(time.time()) - 100
    token = f"nbf_{past_timestamp}"
    assert validate_bearer_token(f"Bearer {token}") == token


def test_validate_bearer_token_not_before_inactive():
    # Future timestamp nbf should raise AuthenticationError
    future_timestamp = int(time.time()) + 1000000
    token = f"worker_nbf_{future_timestamp}"
    with pytest.raises(AuthenticationError, match="Token is not active yet"):
        validate_bearer_token(f"Bearer {token}")


class TestAuthNotBeforeIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_inactive_nbf_token_denied(self):
        future_timestamp = int(time.time()) + 100000
        headers = {"Authorization": f"Bearer worker_nbf_{future_timestamp}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 401
        assert "Token is not active yet" in response.text

    def test_active_nbf_token_allowed(self):
        past_timestamp = int(time.time()) - 500
        headers = {"Authorization": f"bearer worker_nbf_{past_timestamp}"}
        response = self.client.get("/api/v2/agents", headers=headers)
        assert response.status_code == 200
