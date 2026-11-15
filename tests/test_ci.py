"""The CI workflow for this repository: kmctl's own check, prek (ruff, kmctl check, OKF validation) and pytest on every pull request."""

import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CI = WORKFLOWS / "ci.yml"
HOWTO = ROOT / "docs" / "how-to" / "install-the-plugin-and-the-ci-action.md"


def _ci() -> dict[Any, Any]:
    """Parse ci.yml; PyYAML reads the ``on:`` key as True, so put it back under ``on``."""
    data: dict[Any, Any] = yaml.safe_load(CI.read_text())
    data["on"] = data.pop(True)
    return data


def _steps() -> list[dict[str, Any]]:
    """Every step of every job in ci.yml."""
    return [step for job in _ci()["jobs"].values() for step in job["steps"]]


def test_ci_triggers_on_pull_request_and_push_to_main() -> None:
    on = _ci()["on"]

    assert "pull_request" in on
    assert on["push"]["branches"] == ["main"]


# Each CI test job and the directory its pytest step runs.
TEST_JOBS = {
    "kmctl": "packages/kmctl/tests",
    "kmaudit": "packages/kmaudit/tests",
    "repo": "tests",
}


def test_ci_per_package_jobs_run_prek_then_knowledge_then_the_tests() -> None:
    ci = _ci()
    jobs = ci["jobs"]

    assert ci["name"] == "CI"
    assert list(jobs) == [
        "prek",
        "knowledge",
        "kmctl",
        "kmaudit",
        "repo",
        "starter",
        "tests",
    ]
    assert "needs" not in jobs["prek"]
    assert jobs["knowledge"]["needs"] == "prek"
    for name in [*TEST_JOBS, "starter"]:
        assert jobs[name]["needs"] == "knowledge", name


def test_ci_knowledge_job_runs_own_check_with_full_history() -> None:
    [job] = [j for j in _ci()["jobs"].values() if {"uses": "./"} in j["steps"]]
    [checkout] = [s for s in job["steps"] if "checkout" in s.get("uses", "")]

    assert checkout["with"]["fetch-depth"] == 0


def _job_steps(name: str) -> list[dict[str, Any]]:
    """The steps of job ``name`` in ci.yml."""
    steps: list[dict[str, Any]] = _ci()["jobs"][name]["steps"]
    return steps


def _uses(steps: list[dict[str, Any]], action: str) -> int:
    """The index of the step in ``steps`` that uses ``action`` at a pinned ref."""
    [index] = [
        i for i, s in enumerate(steps) if s.get("uses", "").startswith(f"{action}@")
    ]
    return index


def test_ci_prek_job_runs_justfile_version_after_uv() -> None:
    pinned = re.search(r"prek@([\d.]+)", (ROOT / "justfile").read_text())
    steps = _job_steps("prek")
    hooks = _uses(steps, "JasperHG90/toiminnot/actions/prek")

    assert pinned
    assert _uses(steps, "astral-sh/setup-uv") < hooks
    assert steps[hooks]["with"] == {
        "prek_version": pinned.group(1),
        "python_version": "3.12",
    }


def test_ci_per_package_test_jobs_run_the_default_tier_in_their_own_directory() -> None:
    for name, directory in TEST_JOBS.items():
        steps = _job_steps(name)
        tests = steps[_uses(steps, "JasperHG90/toiminnot/actions/pytest")]

        assert tests["with"] == {
            "directory": directory,
            "markers": "not integration",
            "python_version": "3.12",
        }, name


def test_ci_aggregate_tests_job_needs_every_test_job_and_always_runs() -> None:
    """main's ruleset requires prek, knowledge and tests; a check takes its job's name, so none has a name:."""
    jobs = _ci()["jobs"]
    tests = jobs["tests"]

    assert sorted(tests["needs"]) == sorted(TEST_JOBS)
    assert tests["if"] == "always()"
    for name in ["prek", "knowledge", "tests"]:
        assert "name" not in jobs[name], name


def _aggregate_exit(results: dict[str, str]) -> int:
    """Run the tests job's step with each needed job's result and return its exit code."""
    [step] = _job_steps("tests")
    env = {key: str(value) for key, value in step["env"].items()}
    assert env == {
        name.upper(): f"${{{{ needs.{name}.result }}}}" for name in TEST_JOBS
    }
    env = {name.upper(): results[name] for name in TEST_JOBS}
    return subprocess.run(
        ["bash", "-e", "-c", step["run"]],
        env=env,
        capture_output=True,
        check=False,
    ).returncode


@pytest.mark.parametrize("result", ["failure", "skipped", "cancelled"])
@pytest.mark.parametrize("job", list(TEST_JOBS))
def test_ci_aggregate_tests_job_fails_unless_every_test_job_succeeded(
    job: str, result: str
) -> None:
    passed = dict.fromkeys(TEST_JOBS, "success")

    assert _aggregate_exit(passed) == 0
    assert _aggregate_exit({**passed, job: result}) != 0


def _collected(*args: str) -> list[str]:
    """The test ids ``pytest --collect-only`` finds with ``args``, from the root."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if "::" in line]


def test_ci_test_jobs_partition_what_the_gate_collects() -> None:
    """The loop's tests gate and just test run pytest at the root; CI's test jobs must split that, no more, no less."""
    gates = tomllib.loads((ROOT / ".loop" / "config.toml").read_text())["gates"]
    [gate] = [g["command"] for g in gates if g["name"] == "tests"]
    recipe = re.search(
        r"^test:\n\s+(.+)$", (ROOT / "justfile").read_text(), re.MULTILINE
    )
    assert gate == "uv run pytest"
    assert recipe and recipe[1] == gate

    whole = _collected()
    per_job = {}
    for name in TEST_JOBS:
        steps = _job_steps(name)
        directory = steps[_uses(steps, "JasperHG90/toiminnot/actions/pytest")]["with"][
            "directory"
        ]
        per_job[name] = _collected(directory)

    assert all(per_job.values()), {k: len(v) for k, v in per_job.items()}
    assert sum(len(ids) for ids in per_job.values()) == len(whole)
    union = [i for ids in per_job.values() for i in ids]
    assert len(set(union)) == len(union)
    assert set(union) == set(whole)
    assert any(i.startswith("packages/kmctl/") for i in whole)
    assert any(i.startswith("packages/kmaudit/") for i in whole)


def test_ci_actions_pinned_and_uv_cache_off() -> None:
    uses = [s["uses"] for s in _steps() if "uses" in s and s["uses"] != "./"]
    setup_uv = [s for s in _steps() if "setup-uv" in s.get("uses", "")]

    assert uses
    assert all(
        re.fullmatch(r"[\w-]+/[\w-]+(/[\w-]+)*@[0-9a-f]{40}", u) for u in uses
    ), uses
    assert setup_uv
    assert all(s["with"]["enable-cache"] is False for s in setup_uv)


def test_ci_knowledge_yml_gone() -> None:
    assert not (WORKFLOWS / "knowledge.yml").exists()


def test_ci_howto_quoted_workflows_exist() -> None:
    text = " ".join(HOWTO.read_text().split())
    note = re.search(r"The workflow files are quoted from (.+?)\.\s", text)
    shipped = re.search(r"This is (.+?):\s", text)

    assert note and shipped
    cited = re.findall(r"`(\.github/workflows/[\w.-]+)`", note[1] + shipped[1])
    assert cited
    assert [c for c in cited if not (ROOT / c).exists()] == []


def test_ci_prek_hooks_cover_the_gates_and_the_bundle() -> None:
    """prek, which CI runs on every tracked file, lints, formats and checks docs/ and .okf/."""
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    hooks = {h["id"]: h for repo in config["repos"] for h in repo["hooks"]}

    assert hooks["ruff-check"]["entry"] == "uv run ruff check --fix"
    assert hooks["ruff-format"]["entry"] == "uv run ruff format"
    assert hooks["kmctl-check"]["entry"] == "uv run kmctl check --fix"
    assert hooks["okf-validate"]["entry"] == (
        "uv run python tests/vendor/okf/okf_validate.py .okf --strict"
    )
    assert (ROOT / "tests/vendor/okf/okf_validate.py").is_file()
