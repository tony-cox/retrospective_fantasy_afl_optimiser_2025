from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Ensure repo root is importable (for helper modules like scripts/*).
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-perf",
        action="store_true",
        default=False,
        help="Run performance/regression tests (skipped by default).",
    )
    parser.addoption(
        "--update-perf-baseline",
        action="store_true",
        default=False,
        help="Update stored performance baselines for perf tests.",
    )
    parser.addoption(
        "--perf-max-regression-ratio",
        action="store",
        type=float,
        default=1.25,
        help=(
            "Max allowed slowdown vs baseline (median runtime). "
            "Example: 1.25 allows up to 25% slower than the baseline."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "perf: performance/regression tests (opt-in with --run-perf)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-perf"):
        return

    skip_perf = pytest.mark.skip(reason="need --run-perf option to run")
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip_perf)
