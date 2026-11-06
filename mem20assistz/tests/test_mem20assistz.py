"""Hermetic tests for the mem20assistz skeleton slice."""

from __future__ import annotations

import tempfile
import unittest


class TestBranding(unittest.TestCase):
    def test_version_present(self):
        import mem20assistz as pkg
        self.assertTrue(pkg.__version__)
        self.assertIsInstance(pkg.__version__, str)

    def test_members_registry(self):
        import mem20assistz as pkg
        self.assertTrue(pkg.MEMBERS)
        self.assertEqual(len(pkg.MEMBERS), 9)
        self.assertIn("mem20ambientdevicecompanionz", pkg.MEMBERS)


class TestCli(unittest.TestCase):
    def test_version_flag(self):
        from mem20assistz import cli
        self.assertEqual(cli.main(["--version"]), 0)

    def test_members_flag(self):
        from mem20assistz import cli
        self.assertEqual(cli.main(["--members"]), 0)


class TestEstateIntegration(unittest.TestCase):
    def test_estate_context_real_integrations(self):
        from mem20assistz.domain import estate_context
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
