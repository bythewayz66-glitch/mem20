import tempfile
import unittest

from mem20mixedinitiativefocusenginez.domain import (
    blend,
    estate_context,
    focus_health,
    focus_score,
    suggest,
    take_over,
)


class TestFocusEngine(unittest.TestCase):
    def test_focus_score_and_health(self):
        s = focus_score({"priority": 2, "distractions": 1})
        self.assertAlmostEqual(s, 1.0)
        self.assertTrue(focus_health({"priority": 1, "distractions": 0})["healthy"])

    def test_suggest_and_take_over(self):
        ranked = suggest({"distractions": 0}, [{"name": "a", "priority": 1}, {"name": "b", "priority": 3}])
        self.assertEqual(ranked[0]["name"], "b")
        self.assertTrue(take_over(0.8, 0.5))
        self.assertFalse(take_over(0.2, 0.5))

    def test_blend(self):
        b = blend({"priority": 10}, {"priority": 0}, alpha=0.5)
        self.assertEqual(b["blended_priority"], 5.0)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertIn("toolchest_total", ctx)
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("delta_keys", ctx)
            self.assertTrue(ctx.get("engine_status_checked"))


if __name__ == "__main__":
    unittest.main()
