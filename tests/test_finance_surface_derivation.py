"""Regression tests for the finance model's tool-surface derivation.

The finance model used to carry `487 / 129` as a literal and assert against that
literal. That passes forever, including after the server gains or loses a tool,
which is precisely the drift the model exists to catch. These tests pin the
replacement behaviour: the count is READ from docs/surface.json and a moved
surface must fail the model rather than be silently re-asserted.

No network. Everything runs against the real repo files plus temp manifests.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "docs" / "finance" / "compute_model.py"
SURFACE = ROOT / "docs" / "surface.json"
INPUTS = ROOT / "docs" / "finance" / "inputs.json"

SPEC = importlib.util.spec_from_file_location("mem20_compute_model", MODEL_PATH)
assert SPEC is not None and SPEC.loader is not None
model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model)


def _load(path: Path) -> dict:
    with open(path) as fh:
        return json.load(fh)


class SurfaceManifestTests(unittest.TestCase):
    """load_surface() derives and self-verifies the manifest."""

    def test_reads_the_committed_manifest(self) -> None:
        live = model.load_surface()
        self.assertEqual((live["tools"], live["domains"]), (487, 129))
        self.assertEqual(live["path"], "docs/surface.json")
        self.assertEqual(len(live["sha256"]), 64)
        self.assertEqual(live["unwired_tools"], 19)
        self.assertEqual(live["cross_check"]["only_ast"], [])
        self.assertEqual(live["cross_check"]["only_live"], [])

    def test_matches_the_declared_inputs(self) -> None:
        surf = _load(INPUTS)["tool_surface"]
        self.assertEqual((surf["tools"], surf["domains"]), (487, 129))
        self.assertEqual((surf["previous_tools"], surf["previous_domains"]), (311, 39))

    def test_count_is_not_hardcoded_in_the_model(self) -> None:
        """The literal pair must not reappear as a comparison in the source."""
        src = MODEL_PATH.read_text()
        for literal in ("!= 487", "!= 129", "== 487", "== 129"):
            self.assertNotIn(
                literal,
                src,
                "compute_model.py compares against the literal %r again; the "
                "surface must be derived from docs/surface.json" % literal,
            )

    def test_counts_are_internally_consistent(self) -> None:
        s = _load(SURFACE)
        self.assertEqual(sum(s["domain_counts"].values()), s["tools"])
        self.assertEqual(len(s["domain_names"]), s["domains"])
        self.assertEqual(s["cross_check"]["ast_tools"], s["tools"])
        self.assertEqual(s["cross_check"]["ast_domains"], s["domains"])


class DriftDetectionTests(unittest.TestCase):
    """A moved or self-inconsistent manifest must fail, not pass silently."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mem20_finance_"))
        self.manifest = self.tmp / "surface.json"
        shutil.copy(SURFACE, self.manifest)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mutate(self, **changes) -> None:
        s = _load(self.manifest)
        for key, value in changes.items():
            s[key] = value
        with open(self.manifest, "w") as fh:
            json.dump(s, fh)

    def test_moved_surface_fails_the_model(self) -> None:
        """Server gains a tool and a domain: declared 487/129 no longer holds."""
        s = _load(self.manifest)
        self._mutate(
            tools=488,
            domains=130,
            domain_names=s["domain_names"] + ["new_domain"],
            domain_counts=dict(s["domain_counts"], new_domain=1),
            cross_check=dict(s["cross_check"], ast_tools=488, ast_domains=130),
        )
        with self.assertRaises(SystemExit) as caught:
            model.build(dict(_load(INPUTS)), surface_path=str(self.manifest))
        self.assertEqual(caught.exception.code, 1)

    def test_load_surface_accepts_the_mutated_manifest(self) -> None:
        """The mutated manifest is well-formed; only the declared inputs disagree."""
        s = _load(self.manifest)
        self._mutate(
            tools=488,
            domains=130,
            domain_names=s["domain_names"] + ["new_domain"],
            domain_counts=dict(s["domain_counts"], new_domain=1),
            cross_check=dict(s["cross_check"], ast_tools=488, ast_domains=130),
        )
        live = model.load_surface(str(self.manifest))
        self.assertEqual((live["tools"], live["domains"]), (488, 130))

    def test_self_inconsistent_manifest_is_rejected(self) -> None:
        s = _load(self.manifest)
        self._mutate(cross_check=dict(s["cross_check"], ast_tools=999))
        with self.assertRaises(SystemExit) as caught:
            model.load_surface(str(self.manifest))
        self.assertEqual(caught.exception.code, 1)

    def test_unmatched_tools_are_rejected(self) -> None:
        s = _load(self.manifest)
        self._mutate(cross_check=dict(s["cross_check"], only_live=["ghost_tool"]))
        with self.assertRaises(SystemExit) as caught:
            model.load_surface(str(self.manifest))
        self.assertEqual(caught.exception.code, 1)

    def test_domain_name_count_mismatch_is_rejected(self) -> None:
        s = _load(self.manifest)
        self._mutate(domain_names=s["domain_names"][:-1])
        with self.assertRaises(SystemExit) as caught:
            model.load_surface(str(self.manifest))
        self.assertEqual(caught.exception.code, 1)

    def test_domain_counts_must_sum_to_the_tool_count(self) -> None:
        s = _load(self.manifest)
        counts = dict(s["domain_counts"])
        counts[next(iter(counts))] += 1
        self._mutate(domain_counts=counts)
        with self.assertRaises(SystemExit) as caught:
            model.load_surface(str(self.manifest))
        self.assertEqual(caught.exception.code, 1)

    def test_missing_manifest_is_rejected(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            model.load_surface(str(self.tmp / "does-not-exist.json"))
        self.assertEqual(caught.exception.code, 1)


class HouseNumberTests(unittest.TestCase):
    """The four house numbers and the SOM arithmetic still hold."""

    def setUp(self) -> None:
        self.inputs = _load(INPUTS)
        self.out = model.build(self.inputs)

    def test_house_numbers_are_exact(self) -> None:
        house = self.inputs["house_numbers"]
        self.assertEqual(house["blended_acv_usd"], 14000)
        self.assertEqual(house["tam_usd"], 1280000000)
        self.assertEqual(house["sam_usd"], 282000000)
        self.assertEqual(house["som_arr_usd"], 1680000)
        self.assertEqual(self.out["acv"]["blended_usd"], 14000.0)
        self.assertEqual(self.out["market"]["som_arr_usd"], 1680000)

    def test_som_equation_is_written_out(self) -> None:
        self.assertEqual(
            self.out["market"]["som_equation"],
            "120 accounts x $14,000 blended ACV = $1,680,000",
        )

    def test_model_output_records_the_manifest_provenance(self) -> None:
        surf = self.out["tool_surface"]
        self.assertTrue(surf["derived_from_manifest"])
        self.assertEqual(surf["manifest"], "docs/surface.json")
        self.assertEqual(len(surf["manifest_sha256"]), 64)
        self.assertEqual((surf["tools"], surf["domains"]), (487, 129))
        self.assertEqual(surf["unwired_tools"], 19)

    def test_build_is_deterministic(self) -> None:
        self.assertEqual(model.build(_load(INPUTS)), self.out)


if __name__ == "__main__":
    unittest.main()
