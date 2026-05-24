import asyncio
import time
import pytest
from src.agent.executor import AgentExecutor


@pytest.mark.anyio
async def test_executor_max_results():
    executor = AgentExecutor(max_results=3)

    async def mock_handler(agent_id, task):
        return f"result_{task['id']}"

    # Run 4 tasks
    id1 = await executor.execute("agent1", {"id": "1"}, mock_handler)
    id2 = await executor.execute("agent1", {"id": "2"}, mock_handler)
    id3 = await executor.execute("agent1", {"id": "3"}, mock_handler)
    id4 = await executor.execute("agent1", {"id": "4"}, mock_handler)

    # First task result should have been evicted (oldest)
    assert executor.get_result(id1) is None
    # Subsequent task results should be present
    assert executor.get_result(id2) is not None
    assert executor.get_result(id3) is not None
    assert executor.get_result(id4) is not None


@pytest.mark.anyio
async def test_executor_ttl():
    # Set a TTL of 0.05 seconds
    executor = AgentExecutor(ttl=0.05)

    async def mock_handler(agent_id, task):
        return "done"

    exec_id = await executor.execute("agent1", {"id": "1"}, mock_handler)

    # Immediately after, the result should be accessible
    assert executor.get_result(exec_id) is not None

    # Wait for TTL to expire
    await asyncio.sleep(0.06)

    # Result should now be None (pruned lazily)
    assert executor.get_result(exec_id) is None


@pytest.mark.anyio
async def test_executor_shutdown_cleanup():
    executor = AgentExecutor()

    async def mock_handler(agent_id, task):
        return "done"

    exec_id = await executor.execute("agent1", {"id": "1"}, mock_handler)
    assert executor.get_result(exec_id) is not None

    await executor.shutdown()
    assert executor.get_result(exec_id) is None
    assert not executor._results
    assert not executor._timestamps
