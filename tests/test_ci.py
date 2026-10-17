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


def _runs() -> list[str]:
    """The ``run:`` commands of every step in ci.yml, one line each."""
    return [" ".join(s["run"].split()) for s in _steps() if "run" in s]


def test_ci_triggers_on_pull_request_and_push_to_main() -> None:
    on = _ci()["on"]

    assert "pull_request" in on
    assert on["push"]["branches"] == ["main"]


def test_ci_knowledge_job_runs_own_check_with_full_history() -> None:
    [job] = [j for j in _ci()["jobs"].values() if {"uses": "./"} in j["steps"]]
    [checkout] = [s for s in job["steps"] if "checkout" in s.get("uses", "")]

    assert checkout["with"]["fetch-depth"] == 0


def test_ci_prek_job_runs_all_files_at_justfile_version() -> None:
    pinned = re.search(r"prek@([\d.]+)", (ROOT / "justfile").read_text())

    assert pinned
    assert f"uvx prek@{pinned.group(1)} run --all-files" in _runs()


def test_ci_pytest_job_runs_default_suite() -> None:
    tests = [r for r in _runs() if r.startswith("uv run pytest")]

    assert tests == ["uv run pytest"]


def test_ci_actions_pinned_and_uv_cache_off() -> None:
    uses = [s["uses"] for s in _steps() if "uses" in s and s["uses"] != "./"]
    setup_uv = [s for s in _steps() if "setup-uv" in s.get("uses", "")]

    assert uses
    assert all(re.fullmatch(r"[\w-]+/[\w-]+@[0-9a-f]{40}", u) for u in uses), uses
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
