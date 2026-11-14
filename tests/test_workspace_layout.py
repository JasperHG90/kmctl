"""The repository is a uv workspace root that installs nothing, with kmctl and kmaudit under packages/ (ADR 0044)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = ("kmctl", "kmaudit")


def _toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def test_the_root_installs_no_package() -> None:
    """uv never builds the root: [tool.uv] package = false, and the root names no script or package code."""
    root = _toml(ROOT / "pyproject.toml")

    assert root["tool"]["uv"]["package"] is False
    assert "scripts" not in root["project"]
    assert root["project"]["dependencies"] == []
    assert not (ROOT / "src").exists()


def test_the_root_wheel_is_empty() -> None:
    """The root's build-system, there only for the pre-commit hook, builds a wheel with no files."""
    root = _toml(ROOT / "pyproject.toml")

    assert root["build-system"]["build-backend"] == "hatchling.build"
    assert root["tool"]["hatch"]["build"]["targets"]["wheel"] == {
        "bypass-selection": True
    }


def test_every_package_is_a_workspace_member() -> None:
    """The workspace takes every folder under packages/, and both packages are there."""
    root = _toml(ROOT / "pyproject.toml")

    assert root["tool"]["uv"]["workspace"]["members"] == ["packages/*"]
    for name in MEMBERS:
        assert (ROOT / "packages" / name / "pyproject.toml").is_file(), name


@pytest.mark.parametrize("name", MEMBERS)
def test_each_member_is_a_workspace_source_in_the_dev_group(name: str) -> None:
    """Each package comes from the workspace and sits in the root dev group, so uv sync installs it editable."""
    root = _toml(ROOT / "pyproject.toml")
    dev = [dep.split("[")[0] for dep in root["dependency-groups"]["dev"]]

    assert root["tool"]["uv"]["sources"][name] == {"workspace": True}
    assert name in dev


@pytest.mark.parametrize("name", MEMBERS)
def test_each_member_is_a_full_package(name: str) -> None:
    """Each package's pyproject has its own [project] and [build-system], and its code under src/."""
    package = ROOT / "packages" / name
    pyproject = _toml(package / "pyproject.toml")

    assert pyproject["project"]["name"] == name
    assert pyproject["build-system"]["build-backend"] == "hatchling.build"
    assert (package / "src" / name / "__init__.py").is_file()
    assert (package / "tests").is_dir()


def test_kmctl_reads_its_version_from_the_apm_package() -> None:
    """kmctl's version still comes from apm/apm.yml at the root (ADR 0012), two folders up."""
    kmctl = _toml(ROOT / "packages" / "kmctl" / "pyproject.toml")
    path = kmctl["tool"]["hatch"]["version"]["path"]

    assert path == "../../apm/apm.yml"
    assert (ROOT / "packages" / "kmctl" / path).resolve() == ROOT / "apm" / "apm.yml"


def test_one_lock_at_the_root() -> None:
    """The workspace shares the root uv.lock; no package keeps its own."""
    assert (ROOT / "uv.lock").is_file()
    assert not list((ROOT / "packages").glob("*/uv.lock"))
