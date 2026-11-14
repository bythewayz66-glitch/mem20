import tempfile
import unittest

from mem20apishapeshiftinggatewayz.domain import adapt_response, estate_context, schema_diff, transform_payload, version_route


class TestGatewayDomain(unittest.TestCase):
    def test_transform_and_version(self):
        self.assertEqual(transform_payload({"a": 1}, {"a": "b"}), {"b": 1})
        self.assertEqual(version_route("/x", 2), "/v2/x")
        diff = schema_diff({"properties": {"a": {}}}, {"properties": {"b": {}}})
        self.assertIn("a", diff["removed"])
        self.assertEqual(adapt_response({"ok": True}, 3)["_version"], 3)

    def test_estate_context_real_integrations(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = estate_context(d)
            self.assertTrue(ctx.get("engine_status_checked"))
            self.assertTrue(ctx.get("dedup_probe_seen"))
            self.assertIn("toolchest_total", ctx)


if __name__ == "__main__":
    unittest.main()
