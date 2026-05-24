"""Regression tests for TaskScheduler health gates and dependency outages."""

import pytest
import time
import asyncio
from src.orchestrator.scheduler import TaskScheduler


@pytest.mark.anyio
async def test_scheduler_health_gate_success():
    scheduler = TaskScheduler()

    # 1. Enqueue task without dependencies -> should dispatch immediately
    task1 = {"type": "t1", "dependencies": []}
    scheduler.enqueue(task1)
    dispatched = await scheduler.dequeue()
    assert dispatched is not None
    assert dispatched["type"] == "t1"


@pytest.mark.anyio
async def test_scheduler_health_gate_healthy_deps():
    scheduler = TaskScheduler()

    # 2. Enqueue task with healthy dependencies -> should dispatch immediately
    task2 = {"type": "t2", "dependencies": ["database", "redis"]}
    scheduler.enqueue(task2)
    dispatched = await scheduler.dequeue()
    assert dispatched is not None
    assert dispatched["type"] == "t2"


@pytest.mark.anyio
async def test_scheduler_health_gate_outage_deferral():
    scheduler = TaskScheduler()

    # 3. Enqueue task with dependencies, but register an outage
    task3 = {"type": "t3", "dependencies": ["model_api"]}
    scheduler.enqueue(task3)

    # Trigger dependency outage
    scheduler.set_service_health("model_api", healthy=False)

    # Dequeue should defer the task and return None
    dispatched = await scheduler.dequeue()
    assert dispatched is None

    # Verify audit log recorded outage and task deferral
    outage_logs = [log for log in scheduler._audit_log if log["action"] == "service_outage"]
    defer_logs = [log for log in scheduler._audit_log if log["action"] == "task_deferred"]
    assert len(outage_logs) == 1
    assert outage_logs[0]["service"] == "model_api"
    assert len(defer_logs) == 1
    assert "dependency_outage: model_api" in defer_logs[0]["reason"]

    # Verify task was deferred (placed in self._scheduled)
    assert len(scheduler._scheduled) == 1


@pytest.mark.anyio
async def test_scheduler_health_gate_recovery():
    scheduler = TaskScheduler()

    # 4. Enqueue and defer task, then recover the service
    task = {"type": "t4", "dependencies": ["database"]}
    scheduler.enqueue(task)

    scheduler.set_service_health("database", healthy=False)
    dispatched = await scheduler.dequeue()
    assert dispatched is None

    # Service recovered
    scheduler.set_service_health("database", healthy=True)

    # Mock the time expiration of the delay in self._scheduled
    # (rescheduled with a 1.0 second delay, so we overwrite the scheduled time to be in the past)
    for tid in list(scheduler._scheduled.keys()):
        val = scheduler._scheduled[tid]
        scheduler._scheduled[tid] = (val[0], time.time() - 10)

    # Dequeue again -> should pop from scheduled, enqueue, and successfully dispatch
    dispatched = await scheduler.dequeue()
    assert dispatched is not None
    assert dispatched["type"] == "t4"

    # Verify recovery log in audit log
    recovery_logs = [log for log in scheduler._audit_log if log["action"] == "service_recovered"]
    assert len(recovery_logs) == 1
    assert recovery_logs[0]["service"] == "database"
