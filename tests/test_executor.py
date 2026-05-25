import pytest
import asyncio
from src.agent.executor import AgentExecutor

@pytest.mark.anyio
async def test_executor_execute_non_blocking():
    executor = AgentExecutor(max_concurrent=1)
    
    async def slow_handler(agent_id, task):
        await asyncio.sleep(0.1)
        return "done"
        
    start_time = asyncio.get_event_loop().time()
    execution_id = await executor.execute("agent-1", {"id": "task-1"}, slow_handler)
    end_time = asyncio.get_event_loop().time()
    
    # execute should return immediately without waiting 0.1s
    assert end_time - start_time < 0.05
    assert execution_id is not None
    
    # Wait for the background task to finish
    await asyncio.sleep(0.2)
    result = executor.get_result(execution_id)
    assert result["result"] == "done"
