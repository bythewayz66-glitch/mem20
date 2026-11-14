"""Tests for mem20livemodelfusionz."""

from __future__ import annotations

import tempfile
import unittest

from mem20livemodelfusionz.domain import ensemble_vote, estate_context, fuse, fusion_health, select_best, weight_by_confidence


class TestFusion(unittest.TestCase):
    def test_fuse_and_health(self):
        models = [{"outputs": {"a": 1}, "confidence": 0.8}, {"outputs": {"a": 3}, "confidence": 0.2}]
        out = fuse(models)
        self.assertEqual(out["models"], 2)
        self.assertIn("fused", out)
        self.assertEqual(fusion_health(models)["count"], 2)

    def test_weights_select_vote(self):
        models = [{"confidence": 1}, {"confidence": 1}]
        self.assertEqual(weight_by_confidence(models), [0.5, 0.5])
        self.assertEqual(select_best([{"accuracy": 0.1}, {"accuracy": 0.9}], "accuracy")["accuracy"], 0.9)
        self.assertEqual(ensemble_vote(["a", "b", "a"]), "a")

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
