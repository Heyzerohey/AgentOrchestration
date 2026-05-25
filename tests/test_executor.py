import pytest
import asyncio
from src.agent.executor import AgentExecutor

@pytest.mark.anyio
async def test_executor_max_concurrent_validation():
    with pytest.raises(ValueError, match="max_concurrent must be a positive integer"):
        AgentExecutor(max_concurrent=0)
    
    with pytest.raises(ValueError, match="max_concurrent must be a positive integer"):
        AgentExecutor(max_concurrent=-1)
    
    executor = AgentExecutor(max_concurrent=1)
    assert executor.max_concurrent == 1
