import pytest
import asyncio
from src.agent.executor import AgentExecutor


@pytest.mark.anyio
async def test_execute_success():
    executor = AgentExecutor()

    async def mock_handler(agent_id, task):
        return {"output": "success"}

    exec_id = await executor.execute("agent-1", {"id": "task-1"}, mock_handler)
    assert exec_id is not None
    result = executor.get_result(exec_id)
    assert result is not None
    assert result["result"] == {"output": "success"}


@pytest.mark.anyio
async def test_execute_exception():
    executor = AgentExecutor()

    async def mock_handler(agent_id, task):
        raise ValueError("Something went wrong")

    exec_id = await executor.execute("agent-1", {"id": "task-1"}, mock_handler)
    assert exec_id is not None
    result = executor.get_result(exec_id)
    assert result is not None
    assert "error" in result
    assert "Something went wrong" in result["error"]


@pytest.mark.anyio
async def test_execute_cancellation():
    executor = AgentExecutor()
    cancel_event = asyncio.Event()

    async def mock_handler(agent_id, task):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancel_event.set()
            raise

    execute_task = asyncio.create_task(
        executor.execute("agent-1", {"id": "task-1"}, mock_handler)
    )

    await asyncio.sleep(0.05)

    active_ids = list(executor._active_tasks.keys())
    assert len(active_ids) == 1
    exec_id = active_ids[0]

    assert executor.cancel(exec_id)

    with pytest.raises(asyncio.CancelledError):
        await execute_task

    assert cancel_event.is_set()

    result = executor.get_result(exec_id)
    assert result is not None
    assert result.get("status") == "cancelled"
