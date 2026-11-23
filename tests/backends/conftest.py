"""Pytest configuration for backend conformance tests."""

import os
import tempfile
import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--backend",
        action="store",
        default="memory",
        help="Comma-separated list of backends to test (e.g., faiss,memory)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "backend(name): mark test to run only on specific backend"
    )


@pytest.fixture(scope="function")
def temp_store_path() -> str:
    """Create a temporary store path for each test."""
    return tempfile.mkdtemp(prefix="mem20-test-")


@pytest.fixture(autouse=True)
def set_store_path(temp_store_path: str) -> None:
    """Set MEM20_STORE_PATH for all tests."""
    os.environ["MEM20_STORE_PATH"] = temp_store_path
    yield