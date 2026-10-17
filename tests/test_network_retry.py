"""The integration tier for tests that reach GitHub, and the retry on a network error.

The retry tests run a small generated test file in-process with pytester, with
``time.sleep`` patched, so they need no network and do not wait.
"""

import ast
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
#: The tests that run the real kmctl plugin install, which reaches GitHub through APM.
PLUGIN_TESTS = ROOT / "tests" / "test_apm_package.py"
CONFTEST = ROOT / "tests" / "conftest.py"


def _pytest(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _collected(*args: str) -> set[str]:
    out = _pytest("--collect-only", "-q", str(PLUGIN_TESTS), *args)
    assert out.returncode in (0, 5), out.stdout + out.stderr
    return {
        line.split("::")[1].split("[")[0]
        for line in out.stdout.splitlines()
        if "::" in line
    }


def _is_install_call(node: ast.AST) -> bool:
    """An ``apm_install(...)`` call, which runs the real APM against the network."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "apm_install"
    )


def _tests_that_install() -> set[str]:
    """Tests in test_apm_package.py that install kmctl's package with the real APM."""
    tree = ast.parse(PLUGIN_TESTS.read_text())
    return {
        fn.name
        for fn in tree.body
        if isinstance(fn, ast.FunctionDef)
        and fn.name.startswith("test_")
        and any(_is_install_call(n) for n in ast.walk(fn))
    }


def test_tier_registered_and_left_out_of_default_run() -> None:
    pytest_cfg = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["pytest"][
        "ini_options"
    ]
    addopts = pytest_cfg["addopts"]

    assert "--strict-markers" in addopts
    assert addopts[addopts.index("-m") + 1] == "not integration"
    [entry] = [m for m in pytest_cfg["markers"] if m.startswith("integration:")]
    assert ".loop/config.toml" in entry, "the description says where the tier runs"


def test_tier_default_run_collects_no_network_test() -> None:
    assert _collected() & _tests_that_install() == set()


def test_tier_integration_gate_runs_it() -> None:
    gates = tomllib.loads((ROOT / ".loop" / "config.toml").read_text())["gates"]

    assert {"name": "integration", "command": "uv run pytest -m integration"} in gates


def test_tier_unregistered_marker_fails_collection(tmp_path: Path) -> None:
    test = tmp_path / "test_typo.py"
    test.write_text(
        "import pytest\n\n@pytest.mark.integraton\ndef test_x():\n    pass\n"
    )

    out = _pytest("--collect-only", "-c", str(ROOT / "pyproject.toml"), str(test))

    assert out.returncode != 0
    assert "integraton" in out.stdout + out.stderr


def test_marked_every_test_that_runs_the_real_install() -> None:
    installs = _tests_that_install()

    assert len(installs) == 1
    assert installs <= _collected("-m", "integration")


def test_installs_asserted_with_expected_exit_and_output() -> None:
    """apm_install fails the test when APM or kmctl plugin patch fails, so a call needs no check of its own."""
    tree = ast.parse((ROOT / "tests" / "conftest.py").read_text())
    [helper] = [
        fn
        for fn in tree.body
        if isinstance(fn, ast.FunctionDef) and fn.name == "apm_install"
    ]
    asserted = {
        ast.unparse(node.test.left)
        for node in ast.walk(helper)
        if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)
    }

    assert {"proc.returncode", "result.exit_code"} <= asserted


GENERATED = """
import pytest
from pathlib import Path

COUNT = Path(__file__).parent / "count"


@pytest.mark.integration
def test_flaky():
    runs = int(COUNT.read_text()) + 1 if COUNT.exists() else 1
    COUNT.write_text(str(runs))
    output = {outputs}[runs - 1] if runs <= len({outputs}) else ""
    assert not output, output
"""


@pytest.fixture
def run_generated(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch):
    """Run one generated test under the real conftest; return its outcome, runs and sleeps."""
    pytester.makeconftest(CONFTEST.read_text())
    pytester.makeini(
        "[pytest]\naddopts = --strict-markers\nmarkers =\n    integration: test\n"
    )
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    def run(outputs: list[str], marked: bool = True) -> tuple[str, int, list[float]]:
        source = GENERATED.format(outputs=repr(outputs))
        if not marked:
            source = source.replace("@pytest.mark.integration\n", "")
        pytester.makepyfile(source)
        result = pytester.runpytest_inprocess("-p", "no:cacheprovider")
        outcomes = set(result.parseoutcomes()) & {"passed", "failed"}
        assert len(outcomes) == 1, result.outlines
        [outcome] = outcomes
        runs = int((pytester.path / "count").read_text())
        return outcome, runs, sleeps

    return run


NETWORK = "kmctl: claude failed: fatal: unable to access 'https://github.com/x/': "


@pytest.mark.parametrize(
    "error",
    [
        "Could not resolve host: github.com",
        "Failed to connect to github.com port 443",
        "Connection refused",
        "Connection timed out after 300000 milliseconds",
        "Operation timed out",
        "Temporary failure in name resolution",
    ],
)
def test_retry_network_error_twice_then_pass(run_generated, error: str) -> None:
    outcome, runs, sleeps = run_generated([NETWORK + error, NETWORK + error])

    assert (outcome, runs) == ("passed", 3)
    assert len(sleeps) == 2
    assert all(1 <= s <= 10 for s in sleeps), "a few seconds apart"


def test_retry_not_for_another_failure(run_generated) -> None:
    outcome, runs, sleeps = run_generated(["manifest missing", "", ""])

    assert (outcome, runs, sleeps) == ("failed", 1, [])


def test_retry_three_network_failures_still_fail(run_generated) -> None:
    error = NETWORK + "Could not resolve host: github.com"

    outcome, runs, _ = run_generated([error, error, error, ""])

    assert (outcome, runs) == ("failed", 3)


def test_retry_only_in_integration_tier(run_generated) -> None:
    error = NETWORK + "Could not resolve host: github.com"

    outcome, runs, sleeps = run_generated([error, ""], marked=False)

    assert (outcome, runs, sleeps) == ("failed", 1, [])
