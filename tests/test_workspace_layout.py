"""The repository is a uv workspace root that installs nothing, with kmctl and kmaudit under packages/ (ADR 0044)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

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


@pytest.mark.parametrize("name", MEMBERS)
def test_each_member_reads_its_version_from_its_apm_package(name: str) -> None:
    """Each package's version comes from its own apm/apm.yml (ADR 0012, ADR 0045), and the regex reads that file's version."""
    package = ROOT / "packages" / name
    pyproject = _toml(package / "pyproject.toml")
    source = pyproject["tool"]["hatch"]["version"]
    manifest = package / "apm" / "apm.yml"

    assert source["source"] == "regex"
    assert source["path"] == "apm/apm.yml"
    assert {"file": "apm/apm.yml"} in pyproject["tool"]["uv"]["cache-keys"]
    [match] = re.finditer(source["pattern"], manifest.read_text())
    data = yaml.safe_load(manifest.read_text())
    assert data["name"] == name
    assert match.group("version") == str(data["version"])


def test_kmctl_builds_its_package_data_from_its_own_apm_folder() -> None:
    """kmctl's wheel hook and sdist read packages/kmctl/apm, with no path out of the package folder."""
    package = ROOT / "packages" / "kmctl"
    pyproject = _toml(package / "pyproject.toml")
    targets = pyproject["tool"]["hatch"]["build"]["targets"]
    include = targets["wheel"]["hooks"]["custom"]["apm-include"]
    sdist = targets["sdist"]["force-include"]

    assert set(include.values()) == {"kmctl/_skills", "kmctl/_agents", "kmctl/_rules"}
    for source in include:
        assert (package / "apm" / source).is_dir(), source
    for source, target in sdist.items():
        assert source == target and source.startswith("apm/"), source
        assert (package / source).is_dir(), source
    assert "../" not in (package / "pyproject.toml").read_text()
    assert "../" not in (package / "hatch_build.py").read_text()


def test_no_root_apm_folder_and_no_kmaudit_version_file() -> None:
    """kmctl's APM package moved into packages/kmctl/apm and kmaudit's VERSION file into its apm.yml."""
    assert not (ROOT / "apm").exists()
    assert not (ROOT / "packages" / "kmaudit" / "VERSION").exists()
    for harness in ("claude", "antigravity"):
        assert (ROOT / "packages" / "kmctl" / "apm" / harness / "apm.yml").is_file()


def test_one_lock_at_the_root() -> None:
    """The workspace shares the root uv.lock; no package keeps its own."""
    assert (ROOT / "uv.lock").is_file()
    assert not list((ROOT / "packages").glob("*/uv.lock"))
