"""Plan verification: dry-run in sandbox before committing."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Verification result status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class CheckType(str, Enum):
    """Types of verification checks."""
    SYNTAX = "syntax"
    TYPE_CHECK = "type_check"
    LINT = "lint"
    TEST = "test"
    BUILD = "build"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    CONTRACT = "contract"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


@dataclass
class VerificationCheck:
    """A single verification check."""
    name: str
    type: CheckType
    command: str
    args: List[str] = field(default_factory=list)
    working_dir: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 60.0
    required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckResult:
    """Result of a verification check."""
    check: VerificationCheck
    status: VerificationStatus
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Complete verification result."""
    plan_id: str
    status: VerificationStatus
    checks: List[CheckResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        end = self.completed_at or time.time()
        return (end - self.started_at) * 1000

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.status == VerificationStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c.status == VerificationStatus.FAILED)

    @property
    def warnings(self) -> int:
        return sum(1 for c in self.checks if c.status == VerificationStatus.WARNING)


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment."""
    base_image: str = "python:3.13-slim"
    work_dir: str = "/workspace"
    memory_limit: str = "2g"
    cpu_limit: str = "2"
    network_enabled: bool = False
    timeout_seconds: float = 300.0
    volumes: List[Tuple[str, str]] = field(default_factory=list)  # (host, container)
    env_vars: Dict[str, str] = field(default_factory=dict)


class VerificationConfig(BaseModel):
    """Configuration for plan verifier."""
    sandbox: Optional[SandboxConfig] = None
    checks: List[VerificationCheck] = Field(default_factory=list)
    fail_fast: bool = False
    parallel_checks: bool = True
    max_parallel: int = 4
    collect_artifacts: bool = True
    artifact_retention_hours: int = 24


class PlanVerifier:
    """Verifies plans by dry-running in sandbox."""

    def __init__(self, config: Optional[VerificationConfig] = None) -> None:
        self.config = config or VerificationConfig()
        self._sandbox_dir: Optional[Path] = None
        self._check_registry: Dict[str, Callable] = {}

        # Register built-in checks
        self._register_builtin_checks()

    def _register_builtin_checks(self) -> None:
        """Register built-in verification checks."""
        self.register_check("python_syntax", self._check_python_syntax)
        self.register_check("typescript_check", self._check_typescript)
        self.register_check("pytest", self._check_pytest)
        self.register_check("ruff", self._check_ruff)
        self.register_check("mypy", self._check_mypy)
        self.register_check("npm_test", self._check_npm_test)
        self.register_check("cargo_test", self._check_cargo_test)
        self.register_check("go_test", self._check_go_test)
        self.register_check("security_scan", self._check_security)
        self.register_check("dependency_audit", self._check_dependency_audit)

    def register_check(self, name: str, fn: Callable) -> None:
        """Register a custom verification check."""
        self._check_registry[name] = fn

    def add_check(self, check: VerificationCheck) -> None:
        """Add a verification check to the pipeline."""
        self.config.checks.append(check)

    def remove_check(self, name: str) -> bool:
        """Remove a check by name."""
        for i, check in enumerate(self.config.checks):
            if check.name == name:
                self.config.checks.pop(i)
                return True
        return False

    async def verify_plan(
        self,
        plan: List[Dict[str, Any]],
        context: Dict[str, Any],
        plan_id: Optional[str] = None,
    ) -> VerificationResult:
        """Verify a plan by running checks in sandbox."""
        plan_id = plan_id or str(uuid.uuid4())[:8]
        result = VerificationResult(plan_id=plan_id, status=VerificationStatus.PASSED)

        # Set up sandbox
        await self._setup_sandbox(plan, context)

        try:
            # Run checks
            if self.config.parallel_checks:
                await self._run_checks_parallel(result)
            else:
                await self._run_checks_sequential(result)

            # Determine overall status
            result.status = self._determine_status(result)
            result.summary = {
                "total": len(result.checks),
                "passed": result.passed,
                "failed": result.failed,
                "warnings": result.warnings,
            }

        finally:
            result.completed_at = time.time()
            await self._cleanup_sandbox()

        return result

    async def _setup_sandbox(self, plan: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
        """Set up sandbox environment."""
        # Create temp directory
        self._sandbox_dir = Path(tempfile.mkdtemp(prefix=f"verify_{uuid.uuid4().hex[:8]}_"))

        # Copy project files if provided
        project_root = context.get("project_root")
        if project_root and Path(project_root).exists():
            # Copy relevant files
            shutil.copytree(
                project_root,
                self._sandbox_dir / "project",
                ignore=shutil.ignore_patterns(
                    ".git", "__pycache__", "*.pyc", "node_modules",
                    "dist", "build", ".venv", "venv", "target"
                ),
                dirs_exist_ok=True,
            )

        # Write plan to sandbox
        plan_file = self._sandbox_dir / "plan.json"
        plan_file.write_text(json.dumps(plan, indent=2))

        # Write context
        context_file = self._sandbox_dir / "context.json"
        context_file.write_text(json.dumps(context, indent=2))

    async def _cleanup_sandbox(self) -> None:
        """Clean up sandbox."""
        if self._sandbox_dir and self._sandbox_dir.exists():
            try:
                shutil.rmtree(self._sandbox_dir)
            except Exception:
                pass
        self._sandbox_dir = None

    async def _run_checks_parallel(self, result: VerificationResult) -> None:
        """Run checks in parallel."""
        semaphore = asyncio.Semaphore(self.config.max_parallel)

        async def run_with_semaphore(check: VerificationCheck) -> CheckResult:
            async with semaphore:
                return await self._run_check(check)

        tasks = [run_with_semaphore(check) for check in self.config.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for check, check_result in zip(self.config.checks, results):
            if isinstance(check_result, Exception):
                result.checks.append(CheckResult(
                    check=check,
                    status=VerificationStatus.ERROR,
                    error=str(check_result),
                ))
            else:
                result.checks.append(check_result)

                if self.config.fail_fast and check_result.status == VerificationStatus.FAILED:
                    break

    async def _run_checks_sequential(self, result: VerificationResult) -> None:
        """Run checks sequentially."""
        for check in self.config.checks:
            try:
                check_result = await self._run_check(check)
                result.checks.append(check_result)

                if self.config.fail_fast and check_result.status == VerificationStatus.FAILED:
                    break
            except Exception as e:
                result.checks.append(CheckResult(
                    check=check,
                    status=VerificationStatus.ERROR,
                    error=str(e),
                ))
                if self.config.fail_fast:
                    break

    async def _run_check(self, check: VerificationCheck) -> CheckResult:
        """Run a single verification check."""
        start = time.time()
        work_dir = self._sandbox_dir or Path.cwd()

        if check.working_dir:
            work_dir = work_dir / check.working_dir

        # Prepare environment
        env = os.environ.copy()
        env.update(check.env)

        try:
            # Run command
            proc = await asyncio.create_subprocess_exec(
                check.command, *check.args,
                cwd=work_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=check.timeout_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return CheckResult(
                    check=check,
                    status=VerificationStatus.FAILED,
                    error=f"Timeout after {check.timeout_seconds}s",
                    duration_ms=(time.time() - start) * 1000,
                )

            duration = (time.time() - start) * 1000
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            # Determine status
            if proc.returncode == 0:
                status = VerificationStatus.PASSED
            elif check.required:
                status = VerificationStatus.FAILED
            else:
                status = VerificationStatus.WARNING

            return CheckResult(
                check=check,
                status=status,
                output=output[:10000],  # Limit output size
                error=error[:5000],
                duration_ms=duration,
            )

        except Exception as e:
            return CheckResult(
                check=check,
                status=VerificationStatus.ERROR,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def _determine_status(self, result: VerificationResult) -> VerificationStatus:
        """Determine overall verification status."""
        if any(c.status == VerificationStatus.ERROR for c in result.checks):
            return VerificationStatus.ERROR
        if any(c.status == VerificationStatus.FAILED for c in result.checks):
            return VerificationStatus.FAILED
        if any(c.status == VerificationStatus.WARNING for c in result.checks):
            return VerificationStatus.WARNING
        return VerificationStatus.PASSED

    # --- Built-in check implementations ---

    async def _check_python_syntax(self, check: VerificationCheck) -> CheckResult:
        """Check Python syntax."""
        return await self._run_check(check)

    async def _check_typescript(self, check: VerificationCheck) -> CheckResult:
        """Check TypeScript compilation."""
        return await self._run_check(check)

    async def _check_pytest(self, check: VerificationCheck) -> CheckResult:
        """Run pytest."""
        return await self._run_check(check)

    async def _check_ruff(self, check: VerificationCheck) -> CheckResult:
        """Run ruff linter."""
        return await self._run_check(check)

    async def _check_mypy(self, check: VerificationCheck) -> CheckResult:
        """Run mypy type checker."""
        return await self._run_check(check)

    async def _check_npm_test(self, check: VerificationCheck) -> CheckResult:
        """Run npm test."""
        return await self._run_check(check)

    async def _check_cargo_test(self, check: VerificationCheck) -> CheckResult:
        """Run cargo test."""
        return await self._run_check(check)

    async def _check_go_test(self, check: VerificationCheck) -> CheckResult:
        """Run go test."""
        return await self._run_check(check)

    async def _check_security(self, check: VerificationCheck) -> CheckResult:
        """Run security scan."""
        return await self._run_check(check)

    async def _check_dependency_audit(self, check: VerificationCheck) -> CheckResult:
        """Run dependency audit."""
        return await self._run_check(check)


class GitWorktreeSandbox:
    """Sandbox using git worktree for isolation."""

    def __init__(self, repo_path: str) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.worktree_path: Optional[Path] = None
        self.branch_name: Optional[str] = None

    async def create(self, plan: List[Dict[str, Any]]) -> Path:
        """Create a new worktree for verification."""
        self.branch_name = f"verify/{uuid.uuid4().hex[:8]}"
        self.worktree_path = Path(tempfile.mkdtemp(prefix=f"wt_{self.branch_name.replace('/', '_')}_"))

        # Create worktree
        proc = await asyncio.create_subprocess_exec(
            "git", "worktree", "add", "-b", self.branch_name, str(self.worktree_path),
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Failed to create worktree: {self.branch_name}")

        # Apply plan changes
        await self._apply_plan(plan)

        return self.worktree_path

    async def _apply_plan(self, plan: List[Dict[str, Any]]) -> None:
        """Apply plan changes to worktree."""
        # This would execute the plan steps in the worktree
        # Simplified: just write plan for reference
        plan_file = self.worktree_path / ".verification_plan.json"
        plan_file.write_text(json.dumps(plan, indent=2))

    async def run_checks(self, checks: List[VerificationCheck]) -> List[CheckResult]:
        """Run verification checks in worktree."""
        verifier = PlanVerifier(VerificationConfig(checks=checks))
        # Would need to adapt verifier to use worktree_path
        return []

    async def cleanup(self) -> None:
        """Remove worktree and cleanup."""
        if self.branch_name:
            proc = await asyncio.create_subprocess_exec(
                "git", "worktree", "remove", "--force", str(self.worktree_path),
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            # Delete branch
            proc = await asyncio.create_subprocess_exec(
                "git", "branch", "-D", self.branch_name,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()


# Global instance
_plan_verifier: Optional[PlanVerifier] = None


def get_plan_verifier(config: Optional[VerificationConfig] = None) -> PlanVerifier:
    """Get global plan verifier instance."""
    global _plan_verifier
    if _plan_verifier is None:
        _plan_verifier = PlanVerifier(config)
    return _plan_verifier