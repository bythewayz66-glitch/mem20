"""Tests for mem20livingagenteconomyz."""

from __future__ import annotations

import tempfile
import unittest

from mem20livingagenteconomyz.domain import create_economy, earn, estate_context, spend, trade


class TestEconomy(unittest.TestCase):
    def test_economy_flow(self):
        e = create_economy(["a", "b"])
        earn(e, "a", 50, "work")
        self.assertTrue(spend(e, "a", 10, "buy")["ok"])
        self.assertTrue(trade(e, "a", "b", 5)["ok"])
        self.assertGreaterEqual(e["agents"]["b"]["balance"], 105)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = estate_context(td)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
