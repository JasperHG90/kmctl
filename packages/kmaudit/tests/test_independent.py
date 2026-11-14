"""kmaudit is its own package: it imports nothing from kmctl and installs and runs without it."""

import ast
import json
import subprocess
import tomllib
from pathlib import Path

import pytest

from .fixtures.audit_repo import make_repo

PACKAGE = Path(__file__).resolve().parents[1]


def _imports(path: Path) -> set[str]:
    """The top-level module names ``path`` imports."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_no_module_imports_kmctl() -> None:
    offenders = [
        str(p.relative_to(PACKAGE))
        for p in sorted(PACKAGE.rglob("*.py"))
        if "kmctl" in _imports(p)
    ]

    assert offenders == []


def test_dependencies_do_not_name_kmctl_so_imports_stay_its_own() -> None:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    wanted = list(project["dependencies"])
    for extra in project.get("optional-dependencies", {}).values():
        wanted.extend(extra)

    assert [d for d in wanted if d.split("[")[0].split(">")[0].strip() == "kmctl"] == []


@pytest.mark.integration
def test_the_wheel_runs_in_a_venv_without_kmctl(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist), str(PACKAGE)],
        check=True,
        capture_output=True,
        timeout=600,
    )
    (wheel,) = dist.glob("kmaudit-*.whl")
    venv = tmp_path / "venv"
    subprocess.run(
        ["uv", "venv", "--python", "3.12", str(venv)],
        check=True,
        capture_output=True,
        timeout=600,
    )
    python = venv / "bin" / "python"
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(wheel)],
        check=True,
        capture_output=True,
        timeout=600,
    )
    has_kmctl = subprocess.run(
        [
            str(python),
            "-c",
            "import importlib.util; print(importlib.util.find_spec('kmctl') is not None)",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    repo = make_repo(tmp_path / "repo")

    result = subprocess.run(
        [str(venv / "bin" / "kmaudit"), "claims", "todo", "--json"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert has_kmctl == "False"
    assert result.returncode == 0, result.stderr
    sections = {s["id"] for s in json.loads(result.stdout)["sections"]}
    assert "tool#parts" in sections
