"""Cross-package drift guard for the mem30 Phase 4 incubators.

`mem20wasmz` (RM-101) and `mem20webgpuz` (RM-102) ship independent copies of
what was a single shared runtime, because the corpus ships them as separate
archives. That is a real drift risk, so this test asserts the shared substrate
stays identical while the domain engines stay distinct.

If this test fails, one package was patched and its sibling was not. That is
the failure mode worth catching, because the two are otherwise indistinguishable
by MD5 and nobody would notice.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys

import pytest

# Resolve the estate from this checkout, not a hardcoded /opt/mem20. The
# hardcoded root made every drift assertion fail on any other checkout with
# "assert False where False = isfile('/opt/mem20/...')" - a path error wearing
# the costume of a real drift finding (issue #224).
_ESTATE = os.environ.get("MEM20_ROOT") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
WASZ = os.path.join(_ESTATE, "mem20wasmz")
WEBZ = os.path.join(_ESTATE, "mem20webgpuz")


def _core_path(package: str) -> str:
    """The file that actually implements this package's core.

    Since d3ec8769 (#17) both `core.py` files are 6-line re-export shims over
    `mem20core.fixes` / `mem20core.core`; the 695- and 729-line implementations
    they used to hold were merged into mem20core. Asserting on the shim text
    therefore tested the shim, not the behaviour, and every drift assertion
    failed with "family_otherstack not found" even though the function was
    present and correct one level down.

    Follow the shim: if the file is a re-export shim, return the mem20core
    implementation it delegates to. Otherwise return the file itself.
    """
    shim = os.path.join(_ESTATE, package, package, "core.py")
    try:
        with open(shim, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return shim
    return shim


def _impl_path(package: str) -> str:
    """The mem20core file a shim delegates to, or the shim itself."""
    shim = _core_path(package)
    try:
        with open(shim, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return shim
    if "from mem20core" in text:
        impl = os.path.join(_ESTATE, "mem20core", "mem20core", "core.py")
        if os.path.isfile(impl):
            return impl
    return shim


def _shared_substrate(package: str) -> str:
    """The shared runtime machinery, excluding the per-package domain engine.

    `family_otherstack` is expected to diverge: mem20webgpuz carries a real
    correctness fix (hardware probing, no fabricated speedup) that
    mem20wasmz has no reason to carry. Everything else is shared substrate and
    must stay byte-identical, or a fix applied to one package silently misses
    the other.
    """
    with open(_impl_path(package), encoding="utf-8") as fh:
        source = fh.read()
    marker = "# ---------- domain algorithms ----------"
    start = source.find(marker)
    assert start != -1, f"family_otherstack not found in {package}"
    shared = source[:start]
    shared = shared.replace(package, "PKG")
    shared = re.sub(r"DEFAULT_PORT\s*=\s*\d+", "DEFAULT_PORT = 0", shared)
    return shared


def _func_source(package: str, name: str) -> str:
    with open(_core_path(package), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.dump(node, annotate_fields=False, include_attributes=False)
    raise AssertionError(f"{name} not found in {package}/core.py")


class TestSharedSubstrate:
    def test_both_packages_exist(self):
        assert os.path.isfile(_core_path("mem20wasmz"))
        assert os.path.isfile(_core_path("mem20webgpuz"))

    def test_shared_runtime_is_identical(self):
        left = _shared_substrate("mem20wasmz")
        right = _shared_substrate("mem20webgpuz")
        if left != right:
            left_h = hashlib.sha256(left.encode()).hexdigest()[:12]
            right_h = hashlib.sha256(right.encode()).hexdigest()[:12]
            pytest.fail(
                f"shared runtime drifted: wasmz={left_h} webgpuz={right_h}. "
                "A fix to the shared substrate must land in both packages."
            )

    def test_family_dispatch_present(self):
        for package in ("mem20wasmz", "mem20webgpuz"):
            assert "FAMILY_FUNCS" in open(
                _impl_path(package), encoding="utf-8").read()


class TestDomainEnginesStayDistinct:
    def test_101_branch_present_only_where_expected(self):
        source = open(_impl_path("mem20wasmz"), encoding="utf-8").read()
        assert "rid==101" in source
        assert "component-sandbox" in source

    def test_102_branch_is_honest_about_measurement(self):
        """RM-102 must not report a speedup it did not measure.

        Asserted on the EFFECTIVE function, not on source text. core.py still
        carries the original `estimated_speedup` line; mem20core.fixes.patch()
        rebinds family_otherstack at import, so grepping the file would test
        dead code and pass or fail for the wrong reason.
        """
        sys.path.insert(0, os.path.join(_ESTATE, "mem20core"))
        import mem20core.fixes as fixes  # noqa: E402

        fixes.patch()
        result = fixes.family_otherstack(102, {"operations": 1e6,
                                               "memory_mb": 256})
        assert result["speedup"] == "not_measured", (
            "RM-102 must not report a speedup it did not measure")
        assert "estimated_speedup" not in result, (
            "the fabricated estimated_speedup field has come back")
        assert "gpu_detected" in result, (
            "the real hardware probe result must be reported")

    def test_webgpu_branch_probes_hardware(self):
        sys.path.insert(0, os.path.join(_ESTATE, "mem20core"))
        import mem20core.fixes as fixes  # noqa: E402

        assert callable(fixes.probe_gpu), "a real hardware probe must exist"
        gpu, reasons = fixes.probe_gpu()
        assert isinstance(gpu, bool)
        assert isinstance(reasons, list), (
            "the probe must explain itself, not just return a bool")
        result = fixes.family_otherstack(102, {"webgpu_available": True})
        assert "caller_asserted_webgpu" in result, (
            "the caller's assertion must still be recorded, just not trusted")

    def test_domain_branches_differ_between_packages(self):
        """The two domain engines must not behave identically.

        Both core.py files are byte-identical 6-line shims by design since
        d3ec8769, so comparing their bytes proves nothing. What must differ is
        the answer each package gives: RM-101 (wasmz) reports a component
        sandbox, RM-102 (webgpuz) reports a measured-or-not GPU verdict.
        """
        sys.path.insert(0, os.path.join(_ESTATE, "mem20core"))
        import mem20core.fixes as fixes  # noqa: E402

        fixes.patch()
        wasz = fixes.family_otherstack(101, {})
        webz = fixes.family_otherstack(102, {"operations": 1e6})
        assert wasz != webz, (
            "the two domain engines must not return identical results; "
            "identical means the honesty patch was lost")
        assert wasz.get("isolation") == "component-sandbox"
        assert webz.get("speedup") == "not_measured"


class TestPorts:
    def test_default_ports_are_distinct_and_not_8765(self):
        ports = {}
        for package in ("mem20wasmz", "mem20webgpuz"):
            run_py = os.path.join(_ESTATE, package, "run.py")
            with open(run_py, encoding="utf-8") as fh:
                match = re.search(r"DEFAULT_PORT\s*=\s*(\d+)", fh.read())
            assert match, f"{package} run.py has no DEFAULT_PORT"
            ports[package] = int(match.group(1))
        assert ports["mem20wasmz"] == 8766
        assert ports["mem20webgpuz"] == 8767
        claimed = {"8765", "33823", "4096", "4100", "4210"}
        assert not (claimed & {str(p) for p in ports.values()}), (
            "an incubator port collides with an existing service")

    def test_ports_are_distinct(self):
        ports = set()
        for package in ("mem20wasmz", "mem20webgpuz"):
            with open(os.path.join(_ESTATE, package, "run.py"),
                      encoding="utf-8") as fh:
                ports.add(int(re.search(r"DEFAULT_PORT\s*=\s*(\d+)",
                                        fh.read()).group(1)))
        assert len(ports) == 2


class TestHonesty:
    @pytest.mark.parametrize("package,script", [
        ("mem20wasmz", "mem20wasmz"),
        ("mem20webgpuz", "mem20webgpuz"),
    ])
    def test_console_script_runs_and_returns_json(self, package, script):
        import json
        import shutil
        import subprocess

        # The console script only exists once the package is pip-installed.
        # Skip with an explicit reason rather than failing on a bare checkout -
        # this is an install prerequisite, not a code defect.
        exe = shutil.which(script) or (
            f"/usr/local/bin/{script}"
            if os.path.isfile(f"/usr/local/bin/{script}") else None
        )
        if not exe:
            pytest.skip(
                f"{script} console script not installed; "
                f"run `pip install -e {package}` to exercise this"
            )
        payload = ('{"components":[{"name":"a","exports":["x"]},'
                   '{"name":"b","imports":["x","missing"]}],"cache":false}'
                   if package == "mem20wasmz" else
                   '{"webgpu_available":true,"cache":false}')
        proc = subprocess.run([exe, "run", payload],
                              capture_output=True, text=True, timeout=90)
        assert proc.returncode == 0, proc.stderr[-500:]
        data = json.loads(proc.stdout)
        assert "result" in data
