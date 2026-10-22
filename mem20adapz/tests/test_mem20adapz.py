"""Hermetic tests for mem20adapz consolidation."""

from __future__ import annotations

import unittest


class TestAdapz(unittest.TestCase):
    def test_version(self):
        import mem20adapz as pkg
        self.assertTrue(pkg.__version__)

    def test_seven_members(self):
        import mem20adapz as pkg
        self.assertEqual(len(pkg.MEMBERS), 7)
        self.assertEqual(len(pkg.FORMER_PACKAGES), 7)
        self.assertIn("dispatch", pkg.MEMBERS)
        self.assertEqual(
            pkg.MEMBERS["dispatch"], "mem20adaptivedispatchenginez"
        )

    def test_cli(self):
        from mem20adapz import cli
        self.assertEqual(cli.main(["--version"]), 0)
        self.assertEqual(cli.main(["--members"]), 0)


if __name__ == "__main__":
    unittest.main()
