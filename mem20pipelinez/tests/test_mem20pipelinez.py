"""Hermetic tests for the mem20pipelinez skeleton slice."""

from __future__ import annotations

import unittest


class TestBranding(unittest.TestCase):
    def test_version_present(self):
        import mem20pipelinez as pkg
        self.assertTrue(pkg.__version__)
        self.assertIsInstance(pkg.__version__, str)

    def test_members_registry(self):
        import mem20pipelinez as pkg
        self.assertTrue(pkg.MEMBERS)
        self.assertEqual(len(pkg.MEMBERS), 12)
        self.assertIn("mem20assetintakecatalogingandvalidationpipelinez", pkg.MEMBERS)


class TestCli(unittest.TestCase):
    def test_version_flag(self):
        from mem20pipelinez import cli
        self.assertEqual(cli.main(["--version"]), 0)

    def test_members_flag(self):
        from mem20pipelinez import cli
        self.assertEqual(cli.main(["--members"]), 0)


if __name__ == "__main__":
    unittest.main()

class TestDepth(unittest.TestCase):
    def test_report_and_probe(self):
        import mem20pipelinez as pkg
        rep=pkg.pipeline_report(); self.assertTrue(rep["ok"]); self.assertEqual(rep["member_count"],12); self.assertEqual(len(rep["peers"]),6)
        for k,v in rep["peers"].items(): self.assertTrue(v.get("ok"),(k,v.get("error")))
        self.assertTrue(pkg.probe()["ok"])
    def test_estate_context_superset(self):
        import mem20pipelinez as pkg, tempfile, pathlib
        with tempfile.TemporaryDirectory() as td:
            ctx=pkg.estate_context(pathlib.Path(td)/"store")
        self.assertEqual(ctx["member_count"],12); self.assertTrue(ctx["engine_status_checked"])
        self.assertEqual(len(ctx["checks"]),6); self.assertIn("peers_ok",ctx)
    def test_subcommand_status(self):
        from mem20pipelinez import cli
        import io, sys, json
        buf=io.StringIO(); old=sys.stdout; sys.stdout=buf
        try: rc=cli.main(["status"])
        finally: sys.stdout=old
        self.assertEqual(rc,0); d=json.loads(buf.getvalue()); self.assertTrue(d["ok"]); self.assertEqual(len(d["peers"]),6)
