"""The CI workflow for this repository: kmctl's own check, prek and pytest on every pull request."""

import re
from pathlib import Path
from typing import Any

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


def test_ci_pytest_job_runs_default_tier() -> None:
    steps = _job_steps("tests")
    tests = steps[_uses(steps, "JasperHG90/toiminnot/actions/pytest")]

    assert tests["with"] == {
        "directory": "tests",
        "markers": "not integration",
        "python_version": "3.12",
    }


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
