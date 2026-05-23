import pytest
import sys
from src.agent.runtime import AgentRuntime, RuntimeState


def test_agent_runtime_start_stop():
    runtime = AgentRuntime()
    agent_id = "test-agent-1"
    command = [sys.executable, "-c", "import time; time.sleep(5)"]

    assert runtime.start(agent_id, command)
    assert runtime.is_running(agent_id)
    assert runtime.get_state(agent_id) == RuntimeState.RUNNING

    assert runtime.stop(agent_id, timeout=2)
    assert not runtime.is_running(agent_id)
    assert runtime.get_state(agent_id) == RuntimeState.STOPPED


def test_agent_runtime_invalid_timeout():
    runtime = AgentRuntime()
    agent_id = "test-agent-2"
    command = [sys.executable, "-c", "import time; time.sleep(5)"]

    assert runtime.start(agent_id, command)

    with pytest.raises(ValueError, match="Timeout must be positive"):
        runtime.stop(agent_id, timeout=-1)

    with pytest.raises(ValueError, match="Timeout must be positive"):
        runtime.stop(agent_id, timeout=0)

    assert runtime.stop(agent_id, timeout=2)


def test_stop_nonexistent_agent():
    runtime = AgentRuntime()
    assert not runtime.stop("nonexistent-agent")
