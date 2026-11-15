"""``scripts/check_wheel.py``: a built wheel carries what kmctl's pyproject adds from packages/kmctl/apm (ADR 0012, ADR 0044, ADR 0045)."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.check_wheel import expected_entries, missing_entries

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_wheel.py"
SMOKE = ROOT / "scripts" / "smoke_wheel.py"
PYPROJECT = ROOT / "packages" / "kmctl" / "pyproject.toml"
COMPLETE = [
    "kmctl/__init__.py",
    "kmctl/_agents/kmctl-auditor.md",
    "kmctl/_rules/okf-bundle.instructions.md",
    "kmctl/_skills/audit/SKILL.md",
    "kmctl/_skills/handoff/SKILL.md",
]


def _wheel(path: Path, names: list[str]) -> Path:
    """Write a zip with the given member names, standing in for a wheel."""
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, "x")
    return path


def _check(wheel: Path) -> subprocess.CompletedProcess[str]:
    """Run the script on ``wheel`` against kmctl's pyproject.toml."""
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(wheel),
            "--pyproject",
            str(PYPROJECT),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_expected_entries_follow_pyproject() -> None:
    """The package's skills, agents and rules folders, as the build hook's table names them."""
    assert expected_entries(PYPROJECT) == [
        "kmctl/_skills/",
        "kmctl/_agents/",
        "kmctl/_rules/",
    ]


def test_a_complete_wheel_passes(tmp_path: Path) -> None:
    """A wheel holding the skills, the agents and the rules passes."""
    res = _check(_wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", COMPLETE))

    assert res.returncode == 0, res.stderr


@pytest.mark.parametrize(
    "dropped", ["kmctl/_skills/", "kmctl/_agents/", "kmctl/_rules/"]
)
def test_a_wheel_without_an_entry_fails(tmp_path: Path, dropped: str) -> None:
    """A wheel without the skills, the agents or the rules is named, and the script exits 1."""
    names = [n for n in COMPLETE if not n.startswith(dropped)]
    wheel = _wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", names)

    res = _check(wheel)

    assert missing_entries(wheel, expected_entries(PYPROJECT)) == [dropped]
    assert res.returncode == 1
    assert f"lacks {dropped}" in res.stderr


def test_the_default_pyproject_is_kmctl_s(tmp_path: Path) -> None:
    """Run from the repository root with no --pyproject, the script reads packages/kmctl/pyproject.toml."""
    wheel = _wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", COMPLETE)

    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(wheel)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == 0, res.stderr
    assert "kmctl/_rules/" in res.stdout


def _manifest_version(package: str = "kmctl") -> str:
    """The version in ``packages/<package>/apm/apm.yml``, which the package's build reads."""
    text = (ROOT / "packages" / package / "apm" / "apm.yml").read_text()
    [line] = [x for x in text.splitlines() if x.startswith("version: ")]
    return line.removeprefix("version: ").strip()


@pytest.mark.integration
@pytest.mark.parametrize(
    "flags",
    [[], ["--wheel"]],
    ids=["wheel-from-sdist", "wheel-only"],
)
def test_package_build_gives_a_wheel_both_scripts_accept(
    tmp_path: Path, flags: list[str]
) -> None:
    """uv build --package kmctl, with or without --wheel, gives a wheel at apm.yml's version with the skills, agents and rules."""
    version = _manifest_version()
    out = tmp_path / "dist"

    build = subprocess.run(
        ["uv", "build", "-q", "--package", "kmctl", *flags, "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert build.returncode == 0, build.stderr
    [wheel] = out.glob("*.whl")
    assert wheel.name == f"kmctl-{version}-py3-none-any.whl"
    if not flags:
        assert (out / f"kmctl-{version}.tar.gz").is_file()
    names = zipfile.ZipFile(wheel).namelist()
    for folder in ("kmctl/_skills/", "kmctl/_agents/", "kmctl/_rules/"):
        assert any(n.startswith(folder) for n in names), folder
    assert _check(wheel).returncode == 0
    smoke = subprocess.run(
        [sys.executable, str(SMOKE), str(wheel), "--version", version],
        capture_output=True,
        text=True,
        check=False,
    )
    assert smoke.returncode == 0, smoke.stdout + smoke.stderr


KMAUDIT_PYPROJECT = ROOT / "packages" / "kmaudit" / "pyproject.toml"
KMAUDIT_COMPLETE = ["kmaudit/__init__.py", "kmaudit/cli.py", "kmaudit/ui.html"]


def test_package_aware_kmaudit_expects_its_package_and_data_files() -> None:
    """kmaudit has no apm-include table: its wheel must hold the package and its non-Python files."""
    assert expected_entries(KMAUDIT_PYPROJECT) == ["kmaudit/", "kmaudit/ui.html"]


@pytest.mark.parametrize(
    ("names", "code"),
    [
        (KMAUDIT_COMPLETE, 0),
        (["kmaudit/__init__.py", "kmaudit/cli.py"], 1),
    ],
    ids=["complete", "no-ui-html"],
)
def test_package_aware_kmaudit_reads_its_own_pyproject(
    tmp_path: Path, names: list[str], code: int
) -> None:
    """``--package kmaudit`` from the root reads packages/kmaudit/pyproject.toml and checks ui.html."""
    wheel = _wheel(tmp_path / "kmaudit-0.1.0-py3-none-any.whl", names)

    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--package", "kmaudit", str(wheel)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert res.returncode == code, res.stderr
    if code:
        assert "lacks kmaudit/ui.html" in res.stderr


def test_package_aware_kmctl_is_unchanged(tmp_path: Path) -> None:
    """``--package kmctl`` checks what the default always has, and a kmaudit wheel fails it."""
    complete = _wheel(tmp_path / "kmctl-0.1.0-py3-none-any.whl", COMPLETE)
    other = _wheel(tmp_path / "kmaudit-0.1.0-py3-none-any.whl", KMAUDIT_COMPLETE)

    def run(wheel: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--package", "kmctl", str(wheel)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    assert run(complete).returncode == 0
    assert run(other).returncode == 1


@pytest.mark.integration
def test_package_aware_kmaudit_build_passes_both_scripts(tmp_path: Path) -> None:
    """uv build --package kmaudit gives a wheel at its apm.yml's version that both scripts accept."""
    version = _manifest_version("kmaudit")
    out = tmp_path / "dist"

    build = subprocess.run(
        ["uv", "build", "-q", "--package", "kmaudit", "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert build.returncode == 0, build.stderr
    [wheel] = out.glob("*.whl")
    assert wheel.name == f"kmaudit-{version}-py3-none-any.whl"
    for script, extra in ((SCRIPT, []), (SMOKE, ["--version", version])):
        res = subprocess.run(
            [sys.executable, str(script), "--package", "kmaudit", str(wheel), *extra],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode == 0, res.stdout + res.stderr


def test_both_wheels_build_at_their_apm_yml_version(tmp_path: Path) -> None:
    """Each package's wheel carries the version its apm.yml names, and kmctl's holds the skills, agents and rules."""
    for package in ("kmctl", "kmaudit"):
        version = _manifest_version(package)
        out = tmp_path / package
        build = subprocess.run(
            ["uv", "build", "-q", "--wheel", "--package", package, "-o", str(out)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert build.returncode == 0, build.stderr
        [wheel] = out.glob("*.whl")
        assert wheel.name == f"{package}-{version}-py3-none-any.whl"
    names = zipfile.ZipFile(next((tmp_path / "kmctl").glob("*.whl"))).namelist()
    for folder in ("kmctl/_skills/", "kmctl/_agents/", "kmctl/_rules/"):
        assert any(n.startswith(folder) for n in names), folder
