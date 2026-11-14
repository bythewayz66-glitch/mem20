"""Tests for mem20liveprojectdemonstrationenginez."""

from __future__ import annotations

import tempfile
import unittest

from mem20liveprojectdemonstrationenginez.domain import add_step, advance, create_demo, estate_context, progress, start


class TestDemo(unittest.TestCase):
    def test_demo_flow(self):
        d = create_demo("p", steps=[{"t": 1}])
        add_step(d, {"t": 2})
        start(d)
        self.assertEqual(d["status"], "running")
        self.assertTrue(advance(d)["ok"])
        self.assertIn("progress", progress(d))

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as td:
            ctx = estate_context(td)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
