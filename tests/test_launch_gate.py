"""Unit tests for the launch gate's version logic, with no network calls."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mem20_launch_gate", ROOT / "scripts" / "check_launch_gate.py"
)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def served(body: str) -> "gate.FetchResult":
    return gate.FetchResult(gate.SITE, status=200, body=body)


class LaunchGateVersionTests(unittest.TestCase):
    def test_current_version_is_not_treated_as_retired(self) -> None:
        self.assertNotIn("3.1.2", gate.retired_versions_for("3.1.2"))
        self.assertEqual(gate.retired_versions_for("3.1.2"), ("v3.0.0", "3.0.0"))

    def test_retired_versions_for_keeps_genuinely_retired_strings(self) -> None:
        retired = gate.retired_versions_for("9.9.9")
        self.assertIn("v3.0.0", retired)
        self.assertIn("3.0.0", retired)

    def test_gate_version_passes_when_the_served_page_carries_the_current_version(self) -> None:
        report = gate.gate_version(
            served("<h1>mem20 3.1.2</h1><footer>3.1.2</footer>"), "3.1.2"
        )
        self.assertEqual(report["verdict"], gate.VERDICT_PASS, report)
        self.assertIn("3.1.2 x2", report["detail"])

    def test_gate_version_fails_when_a_retired_version_is_still_served(self) -> None:
        report = gate.gate_version(
            served("<h1>mem20 3.1.2</h1><footer>v3.0.0</footer>"), "3.1.2"
        )
        self.assertEqual(report["verdict"], gate.VERDICT_FAIL)
        self.assertIn("v3.0.0", report["detail"])

    def test_gate_version_fails_when_the_current_version_is_missing(self) -> None:
        report = gate.gate_version(served("<h1>mem20</h1>"), "3.1.2")
        self.assertEqual(report["verdict"], gate.VERDICT_FAIL)
        self.assertIn("never mentions current version 3.1.2", report["detail"])


if __name__ == "__main__":
    unittest.main()
