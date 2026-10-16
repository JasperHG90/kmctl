import subprocess
import sys
import time
from pathlib import Path

import pytest
from _pytest.runner import runtestprotocol

pytest_plugins = ("pytester",)

VALIDATOR = Path(__file__).parent / "vendor" / "okf" / "okf_validate.py"

# git's wording for a network failure, as kmctl passes on claude's fatal: and error: lines.
NETWORK_ERRORS = (
    "Could not resolve host",
    "Failed to connect",
    "Connection refused",
    "Connection timed out",
    "Operation timed out",
    "Temporary failure in name resolution",
)
RUNS = 3
RETRY_DELAY_SECONDS = 5


def okf_validate(bundle: Path) -> subprocess.CompletedProcess[str]:
    """Run the pinned okf validator in strict mode on ``bundle``."""
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(bundle), "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )


def _network_failure(reports: list[pytest.TestReport]) -> bool:
    return any(
        r.failed and any(e in r.longreprtext for e in NETWORK_ERRORS) for r in reports
    )


def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> bool | None:
    """Run an integration test up to RUNS times while it fails on a network error.

    Only the last run's reports reach the terminal, so a test that passes on a
    later run is reported as passed, and one that fails RUNS times as failed.
    """
    if item.get_closest_marker("integration") is None:
        return None
    item.ihook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    for run in range(1, RUNS + 1):
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
        if run == RUNS or not _network_failure(reports):
            break
        time.sleep(RETRY_DELAY_SECONDS)
    for report in reports:
        item.ihook.pytest_runtest_logreport(report=report)
    item.ihook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True
