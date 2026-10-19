"""The repository is JasperHG90/kmctl; installs made under its old name are still recognised."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from fixtures.fake_tools import FakeTools
from test_plugin_patch import _kmctl, fakes, home, repo  # noqa: F401

from kmctl import plugin
from scripts.release import APM_DOC, APM_FILES, COPIER, DOC_FILES, HOOKS, set_version

ROOT = Path(__file__).resolve().parents[1]
#: Files that describe or detect what an install from the old name holds.
KEEPS_OLD = {
    "src/kmctl/plugin.py",
    "docs/how-to/install-kmctl-with-apm.md",
    "docs/reference/commands.md",
}
#: The two docs pages may name the old repository only as its package.
OLD_IN_DOCS = re.compile(re.escape(plugin.OLD_REPO) + r"(?!/apm)", re.IGNORECASE)


def _tracked() -> list[str]:
    """Tracked files outside .okf/decisions/ and .loop/."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [f for f in out if not f.startswith((".okf/decisions/", ".loop/"))]


def test_old_name_only_where_it_describes_old_installs() -> None:
    old = plugin.OLD_REPO.lower()
    naming = {
        f
        for f in _tracked()
        if (ROOT / f).is_file() and old in (ROOT / f).read_text(errors="ignore").lower()
    }

    assert {f for f in naming if not f.startswith("tests/")} <= KEEPS_OLD
    for page in KEEPS_OLD - {"src/kmctl/plugin.py"}:
        assert not OLD_IN_DOCS.search((ROOT / page).read_text()), page


def test_new_name_in_entry_hooks_and_generated_files() -> None:
    install = "git+https://github.com/JasperHG90/kmctl"

    assert plugin.new_entry()["git"] == "https://github.com/JasperHG90/kmctl.git"
    assert plugin.HOOK_COMMAND.count(install) == 2
    assert plugin.OLD_REPO not in plugin.HOOK_COMMAND
    assert install in (ROOT / "apm/claude/.apm/hooks/hooks.json").read_text()


def _copy_release_files(dest: Path) -> None:
    """Copy the files ``set_version`` reads and writes into ``dest``."""
    for rel in (*APM_FILES, APM_DOC, *DOC_FILES, COPIER, HOOKS):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dest / rel)


def test_new_name_release_set_moves_install_and_uses_lines(tmp_path: Path) -> None:
    _copy_release_files(tmp_path)

    set_version(tmp_path, "9.8.7")

    texts = "\n".join((tmp_path / rel).read_text() for rel in (*DOC_FILES, APM_DOC))
    assert "uv tool install git+https://github.com/JasperHG90/kmctl@v9.8.7\n" in texts
    assert "- uses: JasperHG90/kmctl@v9.8.7\n" in texts


def test_older_example_left_by_release_set(tmp_path: Path) -> None:
    _copy_release_files(tmp_path)
    example = f"{plugin.OLD_PACKAGE}#v0.3.0"
    assert example in (tmp_path / APM_DOC).read_text()

    set_version(tmp_path, "9.8.7")

    assert example in (tmp_path / APM_DOC).read_text()


@pytest.mark.parametrize("name", [plugin.OLD_REPO, plugin.REPO])
def test_old_install_string_entry_refused_from_either_name(
    repo: Path,  # noqa: F811
    fakes: FakeTools,  # noqa: F811
    name: str,
) -> None:
    (repo / "apm.yml").write_text(
        f"name: x\nversion: 0.1.0\ndependencies:\n  apm:\n    - {name}/apm#v0.3.0\n"
    )

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert f"run apm uninstall {name}/apm," in result.stderr


@pytest.mark.parametrize("name", [plugin.OLD_REPO, plugin.REPO])
def test_old_install_v030_layout_refused_from_either_name(
    repo: Path,  # noqa: F811
    fakes: FakeTools,  # noqa: F811
    name: str,
) -> None:
    entry = {"git": f"https://github.com/{name}.git", "path": "apm", "ref": "v0.3.0"}
    (repo / "apm.yml").write_text(
        f"name: x\nversion: 0.1.0\ndependencies:\n  apm:\n    - {json.dumps(entry)}\n"
    )
    lock = {"repo_url": name.lower(), "name": "kmctl", "virtual_path": "plugin"}
    (repo / "apm.lock.yaml").write_text(yaml.safe_dump({"dependencies": [lock]}))

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert f"run apm uninstall github.com/{name}/apm," in result.stderr


@pytest.mark.parametrize("name", [plugin.OLD_REPO, plugin.REPO])
def test_old_install_v030_lock_alone_refused_from_either_name(
    repo: Path,  # noqa: F811
    fakes: FakeTools,  # noqa: F811
    name: str,
) -> None:
    lock = {"repo_url": name.lower(), "name": "kmctl", "virtual_path": "plugin"}
    (repo / "apm.lock.yaml").write_text(yaml.safe_dump({"dependencies": [lock]}))

    result = _kmctl("plugin", "patch")

    assert result.exit_code == 1
    assert f"run apm uninstall {name}/apm," in result.stderr
