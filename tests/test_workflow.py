import asyncio
import pytest
from src.orchestrator.workflow import WorkflowManager, WorkflowStep, StepStatus


class TestWorkflowManager:
    def setup_method(self):
        self.manager = WorkflowManager()

    @pytest.mark.anyio
    async def test_execute_workflow_sync_handler(self):
        workflow = self.manager.create_workflow("sync_workflow")
        
        def sync_handler():
            return "sync_result"

        step = WorkflowStep("sync_step", sync_handler)
        workflow.add_step(step)

        success = await self.manager.execute_workflow(workflow.id)
        assert success is True
        assert step.status == StepStatus.COMPLETED
        assert step.result == "sync_result"
        assert workflow.status == StepStatus.COMPLETED

    @pytest.mark.anyio
    async def test_execute_workflow_async_handler(self):
        workflow = self.manager.create_workflow("async_workflow")

        async def async_handler():
            await asyncio.sleep(0.01)
            return "async_result"

        step = WorkflowStep("async_step", async_handler)
        workflow.add_step(step)

        success = await self.manager.execute_workflow(workflow.id)
        assert success is True
        assert step.status == StepStatus.COMPLETED
        assert step.result == "async_result"
        assert workflow.status == StepStatus.COMPLETED

    @pytest.mark.anyio
    async def test_execute_workflow_timeout(self):
        workflow = self.manager.create_workflow("timeout_workflow")

        async def slow_handler():
            await asyncio.sleep(0.5)
            return "too_late"

        # Timeout set to 0.05 seconds
        step = WorkflowStep("slow_step", slow_handler, timeout=0.05)
        workflow.add_step(step)

        success = await self.manager.execute_workflow(workflow.id)
        assert success is False
        assert step.status == StepStatus.FAILED
        assert "TimeoutError" in str(step.error) or "timeout" in str(step.error).lower()
        assert workflow.status == StepStatus.FAILED

    @pytest.mark.anyio
    async def test_execute_workflow_retry_success(self):
        workflow = self.manager.create_workflow("retry_success_workflow")

        calls = 0

        async def failing_then_succeeding_handler():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ValueError("Transient error")
            return "success_after_retries"

        # Step allowed to retry 2 times (3 total attempts)
        step = WorkflowStep("retry_step", failing_then_succeeding_handler, retries=2)
        workflow.add_step(step)

        success = await self.manager.execute_workflow(workflow.id)
        assert success is True
        assert step.status == StepStatus.COMPLETED
        assert step.result == "success_after_retries"
        assert calls == 3
        assert workflow.status == StepStatus.COMPLETED

    @pytest.mark.anyio
    async def test_execute_workflow_retry_failure(self):
        workflow = self.manager.create_workflow("retry_failure_workflow")

        calls = 0

        def always_failing_handler():
            nonlocal calls
            calls += 1
            raise ValueError("Persistent error")

        # Step allowed to retry 2 times (3 total attempts)
        step = WorkflowStep("retry_step", always_failing_handler, retries=2)
        workflow.add_step(step)

        success = await self.manager.execute_workflow(workflow.id)
        assert success is False
        assert step.status == StepStatus.FAILED
        assert "Persistent error" in str(step.error)
        assert calls == 3
        assert workflow.status == StepStatus.FAILED

    @pytest.mark.anyio
    async def test_execute_workflow_dependencies(self):
        workflow = self.manager.create_workflow("dependencies_workflow")
        execution_order = []
        
        async def handler1():
            await asyncio.sleep(0.02)
            execution_order.append("step1")
            
        async def handler2():
            execution_order.append("step2")
            
        async def handler3():
            execution_order.append("step3")
            
        step1 = WorkflowStep("step1", handler1)
        step2 = WorkflowStep("step2", handler2, dependencies=["step1"])
        step3 = WorkflowStep("step3", handler3, dependencies=["step1", "step2"])
        
        workflow.add_step(step1).add_step(step2).add_step(step3)
        
        success = await self.manager.execute_workflow(workflow.id)
        assert success is True
        assert execution_order == ["step1", "step2", "step3"]
        
    def test_duplicate_parameter_alias(self):
        workflow = self.manager.create_workflow("alias_workflow")
        workflow.add_parameter_alias("input_data", "param1")
        
        with pytest.raises(ValueError, match="Duplicate parameter alias"):
            workflow.add_parameter_alias("input_data", "param2")
