"""Tests for mem20studioz."""
from __future__ import annotations

import tempfile
import unittest

from mem20studioz.domain import critical_path, estate_context, milestone_progress, resource_allocation, schedule_projects, studio_health


class TestStudioOS(unittest.TestCase):
    def test_scheduling_and_resources(self):
        projects = [{"id": "p1", "priority": 2, "effort": 2}, {"id": "p2", "priority": 1, "effort": 1}]
        sched = schedule_projects(projects, 3)
        self.assertTrue(sched)
        alloc = resource_allocation({"gpu": 2}, [{"id": "d1", "resource": "gpu", "amount": 1, "priority": 1}])
        self.assertEqual(alloc["allocations"]["d1"], 1)
        mp = milestone_progress([{"id": "m1"}, {"id": "m2"}], ["m1"])
        self.assertEqual(mp["completed"], 1)
        self.assertEqual(critical_path(["a", "b", "c"], {"b": ["a"], "c": ["b"]}), 3)
        self.assertGreater(studio_health(projects, 5), 0)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
