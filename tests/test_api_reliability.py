import pytest
from fastapi.testclient import TestClient
from src.api.server import create_app
from src.api.routes import registry
from src.agent.registry import AgentStatus

client = TestClient(create_app())


class TestAPIReliability:
    def setup_method(self):
        # Reset registry to clear registered agents for clean test run
        registry._agents.clear()
        registry._index.clear()

    def test_agent_count_route_resolved(self):
        # Register a couple of agents first to check the count
        res = client.post(
            "/api/v2/agents?name=agent-1&agent_type=worker.processor",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code in (200, 201)

        res = client.post(
            "/api/v2/agents?name=agent-2&agent_type=worker.processor",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code in (200, 201)

        # Assert /api/v2/agents/count works correctly
        res = client.get(
            "/api/v2/agents/count",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code == 200
        assert res.json() == {"count": 2}

    def test_list_agents_invalid_status_query_param(self):
        # Send a query parameter that is not a valid AgentStatus value
        res = client.get(
            "/api/v2/agents?status=INVALID_STATUS_VALUE",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code == 400
        assert "Invalid status" in res.json()["detail"]

    def test_stop_agent_transitions_to_stopped(self):
        # Register an agent
        res = client.post(
            "/api/v2/agents?name=agent-to-stop&agent_type=worker.processor",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code in (200, 201)
        agent_id = res.json()["agent_id"]

        # Assert that the initial status is 'pending'
        agent = registry.get(agent_id)
        assert agent["status"] == AgentStatus.PENDING.value

        # Post to /api/v2/agents/{agent_id}/stop
        res = client.post(
            f"/api/v2/agents/{agent_id}/stop",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code == 200
        assert res.json() == {"status": "stopped"}

        # Verify registry shows STOPPED status
        agent = registry.get(agent_id)
        assert agent["status"] == AgentStatus.STOPPED.value

    def test_agent_id_normalization(self):
        # Register an agent
        res = client.post(
            "/api/v2/agents?name=agent-norm&agent_type=worker.processor",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code in (200, 201)
        agent_id = res.json()["agent_id"]

        # Assert we can get it with uppercase ID
        res = client.get(
            f"/api/v2/agents/  {agent_id.upper()}  ",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code == 200
        assert res.json()["id"] == agent_id

        # Delete it with mixed case
        res = client.delete(
            f"/api/v2/agents/{agent_id.upper()}",
            headers={"Authorization": "Bearer token.user.key"}
        )
        assert res.status_code == 200
