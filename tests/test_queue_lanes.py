"""Regression tests for issue #5015 — separate scheduled and immediate queue lanes."""

import asyncio
import time
from unittest.mock import patch

import pytest

from src.orchestrator.scheduler import TaskScheduler


class TestQueueLanes:
    """Tests that verify scheduled and immediate tasks live in separate lanes."""

    def setup_method(self):
        self.scheduler = TaskScheduler()

    # ── Scheduled tasks fire after delay ──────────────────────────────

    def test_scheduled_task_not_available_before_delay(self):
        """A scheduled task must NOT appear in dequeue before its delay."""
        self.scheduler.schedule({"type": "deferred"}, delay=10.0)
        task = asyncio.run(self.scheduler.dequeue())
        assert task is None

    def test_scheduled_task_fires_after_delay(self):
        """A scheduled task MUST appear in dequeue once the delay expires."""
        self.scheduler.schedule({"type": "deferred"}, delay=0.05)
        time.sleep(0.06)
        task = asyncio.run(self.scheduler.dequeue())
        assert task is not None
        assert task["type"] == "deferred"

    def test_scheduled_task_stores_correct_metadata(self):
        """schedule() must persist the full task dict, not just a timestamp."""
        tid = self.scheduler.schedule(
            {"type": "meta", "payload": {"key": "val"}},
            delay=0.01,
        )
        time.sleep(0.02)
        task = asyncio.run(self.scheduler.dequeue())
        assert task is not None
        assert task["type"] == "meta"
        assert task["payload"] == {"key": "val"}
        assert task["id"] == tid

    # ── Immediate tasks are not starved ───────────────────────────────

    def test_immediate_task_dequeued_before_scheduled(self):
        """Immediate tasks must be served before matured scheduled tasks."""
        # Schedule a task with zero delay so it matures immediately
        self.scheduler.schedule({"type": "scheduled"}, delay=0.0)
        # Enqueue an immediate task
        self.scheduler.enqueue({"type": "immediate"})
        task = asyncio.run(self.scheduler.dequeue())
        assert task is not None
        assert task["type"] == "immediate", (
            "Immediate task must be dequeued before scheduled task"
        )

    def test_immediate_tasks_not_blocked_by_many_scheduled(self):
        """Even with many matured scheduled tasks, immediate tasks come first."""
        for i in range(50):
            self.scheduler.schedule({"type": "scheduled", "i": i}, delay=0.0)
        self.scheduler.enqueue({"type": "immediate"})
        task = asyncio.run(self.scheduler.dequeue())
        assert task["type"] == "immediate"

    def test_scheduled_tasks_available_after_immediates_drained(self):
        """Once all immediate tasks are consumed, scheduled ones are served."""
        self.scheduler.schedule({"type": "scheduled"}, delay=0.0)
        self.scheduler.enqueue({"type": "immediate"})

        t1 = asyncio.run(self.scheduler.dequeue())
        assert t1["type"] == "immediate"

        t2 = asyncio.run(self.scheduler.dequeue())
        assert t2 is not None
        assert t2["type"] == "scheduled"

    # ── Duplicate scheduled runs are prevented ────────────────────────

    def test_no_duplicate_scheduled_promotion(self):
        """A scheduled task must only be promoted once, even across dequeues."""
        tid = self.scheduler.schedule({"type": "once"}, delay=0.0)

        # First dequeue promotes and returns the task
        t1 = asyncio.run(self.scheduler.dequeue())
        assert t1 is not None
        assert t1["type"] == "once"

        # Second dequeue must NOT return the same task again
        t2 = asyncio.run(self.scheduler.dequeue())
        assert t2 is None

    def test_duplicate_guard_survives_clock_skew(self):
        """Simulate clock skew: even if _promote_expired runs twice, no dup."""
        tid = self.scheduler.schedule({"type": "skew"}, delay=0.0)
        # Manually promote
        self.scheduler._promote_expired()
        # Force the task back into _scheduled (simulating clock skew re-add)
        self.scheduler._scheduled[tid] = {
            "task": {"type": "skew", "id": tid},
            "fire_at": 0,
            "queue": "default",
            "priority": 0,
        }
        # Promote again — the dedup set should prevent a second enqueue
        self.scheduler._promote_expired()
        sched_q = self.scheduler._scheduled_queue_name("default")
        assert len(self.scheduler._queues[sched_q]) == 1

    # ── Queue and priority routing ────────────────────────────────────

    def test_scheduled_task_routed_to_correct_queue(self):
        """Scheduled tasks must land in the correct queue's scheduled lane."""
        self.scheduler.schedule({"type": "q1"}, delay=0.0, queue="fast")
        task = asyncio.run(self.scheduler.dequeue(queue="fast"))
        assert task is not None
        assert task["type"] == "q1"
        # Must not appear in default queue
        task2 = asyncio.run(self.scheduler.dequeue(queue="default"))
        assert task2 is None

    def test_scheduled_task_respects_priority(self):
        """Higher-priority scheduled tasks should be dequeued first."""
        self.scheduler.schedule({"type": "low"}, delay=0.0, priority=1)
        self.scheduler.schedule({"type": "high"}, delay=0.0, priority=10)
        # Drain immediates (none), get from scheduled lane
        t1 = asyncio.run(self.scheduler.dequeue())
        assert t1["type"] == "high"
        t2 = asyncio.run(self.scheduler.dequeue())
        assert t2["type"] == "low"
