import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.orchestrator.engine import OrchestrationEngine


@pytest.mark.anyio
async def test_idempotent_task_execution():
    # Mock registry
    mock_registry = MagicMock()
    mock_agent = MagicMock()
    mock_registry.get.return_value = mock_agent
    
    # Create engine
    engine = OrchestrationEngine()
    engine.registry = mock_registry
    
    # Mock hooks
    pre_hook = AsyncMock()
    post_hook = AsyncMock()
    on_error_hook = AsyncMock()
    
    engine.register_hook("pre_execute", pre_hook)
    engine.register_hook("post_execute", post_hook)
    engine.register_hook("on_error", on_error_hook)
    
    # Task definition
    task = {
        "id": "task-abc",
        "target_agent": "agent-123"
    }
    
    # First execution
    await engine._execute_task(task)
    
    assert engine.is_finalized("task-abc") is True
    assert pre_hook.call_count == 1
    assert post_hook.call_count == 1
    assert on_error_hook.call_count == 0
    
    # Reset call counts
    pre_hook.reset_mock()
    post_hook.reset_mock()
    
    # Second execution (duplicate terminal event)
    await engine._execute_task(task)
    
    # Hooks should not run again
    assert pre_hook.call_count == 0
    assert post_hook.call_count == 0
    assert on_error_hook.call_count == 0
