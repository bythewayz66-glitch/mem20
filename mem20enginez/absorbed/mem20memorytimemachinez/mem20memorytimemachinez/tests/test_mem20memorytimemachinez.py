"""Tests for mem20memorytimemachinez."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mem20memorytimemachinez.domain import (
    checkpoint_series,
    diff,
    estate_context,
    replay,
    rewind,
    snapshot,
    timeline,
)


class TestTimeMachineDomain(unittest.TestCase):
    def test_snapshot_rewind_replay_diff_timeline(self):
        s0 = snapshot({"a": 1}, label="s0")
        s1 = snapshot({"a": 2, "b": 3}, label="s1")
        snaps = [s0, s1]
        self.assertEqual(rewind(snaps, 0), {"a": 1})
        self.assertIsNone(rewind(snaps, 9))
        self.assertEqual(replay(snaps), [{"a": 1}, {"a": 2, "b": 3}])
        self.assertEqual(diff({"a": 1}, {"a": 2, "b": 3}), {"a": {"from": 1, "to": 2}, "b": {"from": None, "to": 3}})
        tl = timeline(snaps)
        self.assertEqual([t["label"] for t in tl], ["s0", "s1"])

    def test_checkpoint_series(self):
        snaps = checkpoint_series({"x": 0}, [{"x": 1}, {"y": 2}])
        self.assertEqual(len(snaps), 3)
        self.assertEqual(snaps[-1]["state"]["x"], 1)
        self.assertEqual(snaps[-1]["state"]["y"], 2)

    def test_snapshot_with_engine_store(self):
        with tempfile.TemporaryDirectory() as d:
            s = snapshot({"k": "v"}, label="with-engine", store_path=d)
            self.assertEqual(s["state"], {"k": "v"})
            self.assertIn("engine_health", s)
            self.assertIsInstance(s["engine_health"], dict)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertIn("path_scripts", ctx)
            self.assertIn("toolchest_total", ctx)
            self.assertIsInstance(ctx["toolchest_total"], int)
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("focus_probe", ctx)
            self.assertTrue(ctx.get("engine_status_checked"))

    def test_cli_snapshot(self):
        from mem20memorytimemachinez.domain import main
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["snapshot", "--label", "t", "--state", '{"n":1}'])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["state"]["n"], 1)
        self.assertEqual(data["label"], "t")


if __name__ == "__main__":
    unittest.main()
