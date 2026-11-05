"""Tests for mem20aipipelinecostoptimizerz."""
from __future__ import annotations

import tempfile
import unittest

from mem20aipipelinecostoptimizerz.domain import bottleneck, cost_breakdown, estate_context, optimize_throughput, pipeline_cost, stage_cost


class TestCostOptimizer(unittest.TestCase):
    def test_stage_and_pipeline(self):
        stages = [{"id": "a", "base_cost": 1.0, "cost_per_unit": 0.1}, {"id": "b", "base_cost": 0.5, "cost_per_unit": 0.2}]
        self.assertAlmostEqual(stage_cost(stages[0], 10), 2.0, places=3)
        self.assertAlmostEqual(pipeline_cost(stages, 10), 4.5, places=3)
        self.assertEqual(bottleneck(stages, {"a": 5, "b": 2})[0], "b")
        self.assertGreater(optimize_throughput(stages, 10.0), 0)
        self.assertEqual(len(cost_breakdown(stages, 1)), 2)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
