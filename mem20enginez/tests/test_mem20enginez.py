"""Compatibility tests for mem20enginez (assimilated)."""
from __future__ import annotations

import unittest


class TestBranding(unittest.TestCase):
    def test_version_present(self):
        from mem20enginez.mem20enginez import __version__, MEMBERS
        self.assertTrue(__version__)
        self.assertIsInstance(__version__, str)
        self.assertTrue(MEMBERS)
        # assimilated absorbed members
        self.assertGreaterEqual(len(MEMBERS), 30)
        self.assertIn("mem20mixedinitiativefocusenginez", MEMBERS)

    def test_members_registry(self):
        from mem20enginez.mem20enginez import MEMBERS
        self.assertGreaterEqual(len(MEMBERS), 30)
        self.assertEqual(len(MEMBERS), len(set(MEMBERS)))


class TestCli(unittest.TestCase):
    def test_version_flag(self):
        from mem20enginez.mem20enginez.runtime import main
        self.assertEqual(main(["--version"]), 0)

    def test_members_flag(self):
        from mem20enginez.mem20enginez.runtime import main
        self.assertEqual(main(["--members"]), 0)


if __name__ == "__main__":
    unittest.main()
