"""Hermetic tests for the mem20selfz skeleton slice."""

from __future__ import annotations

import unittest


class TestBranding(unittest.TestCase):
    def test_version_present(self):
        import mem20selfz as pkg
        self.assertTrue(pkg.__version__)
        self.assertIsInstance(pkg.__version__, str)

    def test_members_registry(self):
        import mem20selfz as pkg
        self.assertTrue(pkg.MEMBERS)
        self.assertEqual(len(pkg.MEMBERS), 16)
        self.assertIn("mem202dand3dartproductionoptimizationpipelinez", pkg.MEMBERS)


class TestCli(unittest.TestCase):
    def test_version_flag(self):
        from mem20selfz import cli
        self.assertEqual(cli.main(["--version"]), 0)

    def test_members_flag(self):
        from mem20selfz import cli
        self.assertEqual(cli.main(["--members"]), 0)


if __name__ == "__main__":
    unittest.main()

def test_estate_context_real_integrations(tmp_path):
    import importlib
    m = importlib.import_module("mem20selfz.domain")
    ctx = m.estate_context(tmp_path / "store")
    assert ctx["engine_status_checked"] is True
    assert ctx["work_recorded"] is True
    assert ctx["path_scripts"] >= 0
    assert "inventory_keys" in ctx
    assert isinstance(ctx["focus_score"], float)
    assert ctx["sitemap_skips_cache"] is True

