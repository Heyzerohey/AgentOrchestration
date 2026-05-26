import pytest
import asyncio
from src.orchestrator.engine import OrchestrationEngine

@pytest.mark.anyio
async def test_delegation_depth_bound():
    engine = OrchestrationEngine(max_delegation_depth=2)
    
    # We will mock the registry and execution to just track calls
    executed_tasks = []
    
    async def mock_run_agent_task(agent, task):
        executed_tasks.append(task)
        return {"status": "completed"}
    
    engine._run_agent_task = mock_run_agent_task
    
    # Mock registry so agent lookup doesn't fail
    engine.registry.register("test-agent", "worker.processor")
    agent_id = list(engine.registry._agents.keys())[0]
    
    task_1 = {"id": "task-1", "target_agent": agent_id, "_delegation_depth": 0}
    await engine._execute_task(task_1)
    assert len(executed_tasks) == 1
    assert executed_tasks[0]["_delegation_depth"] == 1
    
    task_2 = {"id": "task-2", "target_agent": agent_id, "_delegation_depth": 1}
    await engine._execute_task(task_2)
    assert len(executed_tasks) == 2
    assert executed_tasks[1]["_delegation_depth"] == 2
    
    # Depth 2 should be rejected because max is 2
    task_3 = {"id": "task-3", "target_agent": agent_id, "_delegation_depth": 2}
    await engine._execute_task(task_3)
    # Shouldn't append
    assert len(executed_tasks) == 2
