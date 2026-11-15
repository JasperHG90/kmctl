"""The release version: one source per package in its ``apm/apm.yml``, and ``scripts/release.py`` (ADR 0012, ADR 0045).

``packages/kmctl/pyproject.toml`` reads the version from ``packages/kmctl/apm/apm.yml``,
kmctl's APM package (ADR 0014), so a build needs no git history. ``scripts/release.py`` reads, writes and
compares that version for the release workflows, and points the docs' install
lines at the release tag. It never commits or tags.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

from scripts.release import (
    APM_DOC,
    APM_FILES,
    COPIER,
    DOC_FILES,
    HOOKS,
    KMAUDIT_CLAUDE,
    KMAUDIT_MANIFEST,
    MANIFEST,
    OLD_MANIFEST,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release.py"
#: kmctl's package, whose pyproject reads the version from its own apm/ (ADR 0045).
KMCTL = Path("packages/kmctl")
GIT = ["git", "-c", "user.email=o@e.com", "-c", "user.name=O"]
#: Every release after v0.12.2 builds kmctl from this folder (ADR 0044).
SUBDIRECTORY = "#subdirectory=packages/kmctl"
# The six lines `set` points at the release tag, as they start in the docs.
INSTALL_RE = re.compile(
    r"^\s*uv tool install git\+https://github\.com/JasperHG90/kmctl(@[^\s#]+)?"
    r"(#subdirectory=packages/kmctl)?$",
    re.MULTILINE,
)
USES_RE = re.compile(r"^\s*- uses: JasperHG90/kmctl@(\S+)$", re.MULTILINE)


def _manifest_version(root: Path) -> str:
    """Return the version ``packages/kmctl/apm/apm.yml`` under ``root`` declares."""
    return _apm_version(root / MANIFEST)


def _build(project: Path, out: Path) -> list[str]:
    """Build ``project``'s wheel and sdist into ``out`` and return their file names."""
    res = subprocess.run(
        ["uv", "build", "-q", "-o", str(out), str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    return sorted(p.name for p in out.iterdir() if p.suffix in (".whl", ".gz"))


def test_version_source_is_the_apm_package() -> None:
    """kmctl's ``pyproject.toml`` sets no fixed version; hatchling's regex source reads its apm/apm.yml."""
    data = tomllib.loads((ROOT / KMCTL / "pyproject.toml").read_text())
    manifest = "apm/apm.yml"
    assert KMCTL / manifest == MANIFEST

    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    source = data["tool"]["hatch"]["version"]
    assert source["source"] == "regex"
    assert source["path"] == manifest
    # A local uv run rebuilds kmctl when the manifest changes.
    assert {"file": manifest} in data["tool"]["uv"]["cache-keys"]
    assert {"file": "pyproject.toml"} in data["tool"]["uv"]["cache-keys"]


def test_version_source_builds_the_manifest_version(tmp_path: Path) -> None:
    """``uv build`` of kmctl's package gives a wheel and sdist at its apm.yml's version."""
    version = _manifest_version(ROOT)

    names = _build(ROOT / KMCTL, tmp_path)

    assert names == [f"kmctl-{version}-py3-none-any.whl", f"kmctl-{version}.tar.gz"]


def test_version_source_follows_a_changed_manifest(tmp_path: Path) -> None:
    """A copy of kmctl's package with its apm.yml at another version builds that version."""
    project = tmp_path / "project"
    project.mkdir()
    shutil.copytree(
        ROOT / KMCTL,
        project / KMCTL,
        ignore=shutil.ignore_patterns("__pycache__", "tests"),
    )
    _set_apm_version(project / MANIFEST, "9.8.7")

    names = _build(project / KMCTL, tmp_path / "dist")

    assert names == ["kmctl-9.8.7-py3-none-any.whl", "kmctl-9.8.7.tar.gz"]


def _repo(tmp_path: Path, version: str = "0.1.0") -> Path:
    """A git repository holding this repository's apm.yml files, copier.yml and the docs `set` edits."""
    root = tmp_path / "repo"
    for rel in (*APM_FILES, *DOC_FILES, APM_DOC, COPIER, HOOKS):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, root / rel)
    for rel in APM_FILES:
        _set_apm_version(root / rel, version)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "init"], cwd=root, check=True)
    return root


def _apm_version(path: Path) -> str:
    """The top-level ``version:`` of the apm.yml at ``path``."""
    return str(yaml.safe_load(path.read_text())["version"])


def _set_apm_version(path: Path, version: str) -> None:
    """Rewrite the top-level ``version:`` line of the apm.yml at ``path``."""
    path.write_text(
        re.sub(
            r"^version: .*$",
            f"version: {version}",
            path.read_text(),
            flags=re.MULTILINE,
        )
    )


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run ``scripts/release.py`` against ``root``."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--repo", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


def _refs(root: Path) -> list[str | None]:
    """The refs the six install lines name, in file order (None for no ref)."""
    refs: list[str | None] = []
    for rel in DOC_FILES:
        text = (root / rel).read_text()
        refs += [
            m.group(1)[1:] if m.group(1) else None for m in INSTALL_RE.finditer(text)
        ]
        refs += [m.group(1) for m in USES_RE.finditer(text)]
    return refs


def test_release_py_current_prints_the_manifest_version(tmp_path: Path) -> None:
    """``current`` prints packages/kmctl/apm/apm.yml's version and nothing else."""
    res = _run(_repo(tmp_path, version="0.2.0a1"), "current")

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.2.0a1\n"


def test_release_py_docs_start_with_six_install_lines() -> None:
    """The docs this repository ships hold the six lines `set` rewrites."""
    assert len(_refs(ROOT)) == 6


def test_release_py_set_writes_the_version_and_the_six_doc_lines(
    tmp_path: Path,
) -> None:
    """``set`` writes the version, keeps the package apm.yml's other lines and pins each doc line.

    The target is far past any real release, so it never equals the repository's version.
    """
    root = _repo(tmp_path)
    before = yaml.safe_load((root / MANIFEST).read_text())

    res = _run(root, "set", "9.9.9")

    assert res.returncode == 0, res.stderr
    assert yaml.safe_load((root / MANIFEST).read_text()) == {
        **before,
        "version": "9.9.9",
    }
    changed = set((root / MANIFEST).read_text().splitlines()) ^ set(
        (ROOT / MANIFEST).read_text().splitlines()
    )
    assert changed == {f"version: {_manifest_version(ROOT)}", "version: 9.9.9"}
    assert _refs(root) == ["v9.9.9"] * 6
    assert res.stdout.splitlines() == [
        f"wrote {p}" for p in (*APM_FILES, *DOC_FILES, APM_DOC, COPIER, HOOKS)
    ]


def test_release_py_set_writes_the_apm_version_into_both_apm_yml_files(
    tmp_path: Path,
) -> None:
    """``set 0.2.0`` leaves every kmctl apm.yml file at 0.2.0, the rest as it was."""
    root = _repo(tmp_path)
    before = {rel: (root / rel).read_text() for rel in APM_FILES}

    res = _run(root, "set", "0.2.0")

    assert res.returncode == 0, res.stderr
    assert _manifest_version(root) == "0.2.0"
    assert {rel.as_posix(): _apm_version(root / rel) for rel in APM_FILES} == {
        "apm.yml": "0.2.0",
        "packages/kmctl/apm/apm.yml": "0.2.0",
        "packages/kmctl/apm/claude/apm.yml": "0.2.0",
        "packages/kmctl/apm/antigravity/apm.yml": "0.2.0",
    }
    assert not (root / OLD_MANIFEST).exists()
    for rel, text in before.items():
        changed = set((root / rel).read_text().splitlines()) ^ set(text.splitlines())
        assert changed == {"version: 0.1.0", "version: 0.2.0"}, rel
    assert _run(root, "current").stdout == "0.2.0\n"


def test_release_py_current_refuses_a_differing_apm_version(tmp_path: Path) -> None:
    """``current`` exits nonzero when the root apm.yml's version differs from the package's."""
    root = _repo(tmp_path, version="0.2.0")
    _set_apm_version(root / "apm.yml", "0.1.9")

    res = _run(root, "current")

    assert res.returncode == 1
    assert res.stdout == ""
    assert (
        "apm.yml has version 0.1.9 but packages/kmctl/apm/apm.yml has 0.2.0"
        in res.stderr
    )
    assert "scripts/release.py set 0.2.0" in res.stderr


def test_release_py_current_refuses_a_missing_apm_version(tmp_path: Path) -> None:
    """``current`` exits nonzero when the package's apm.yml is gone or the root apm.yml is.

    It never falls back to the old apm/apm.yml, which only ``manifest`` reads.
    """
    root = _repo(tmp_path)
    (root / "apm.yml").unlink()
    assert "apm.yml has version none" in _run(root, "current").stderr
    (root / OLD_MANIFEST).parent.mkdir()
    shutil.move(root / MANIFEST, root / OLD_MANIFEST)

    res = _run(root, "current")

    assert res.returncode == 1
    assert "packages/kmctl/apm/apm.yml has no top-level version: line" in res.stderr


def test_release_py_manifest_reads_a_before_commit_whose_root_apm_yml_differs(
    tmp_path: Path,
) -> None:
    """``manifest`` prints the package apm.yml's version even when the root apm.yml differs or is gone.

    release-tag.yml reads the before commit this way, so an old commit whose
    copies disagree still gives its version to ``compare``.
    """
    root = _repo(tmp_path, version="0.3.0")
    _set_apm_version(root / "apm.yml", "0.2.9")

    res = _run(root, "manifest")

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.3.0\n"
    (root / "apm.yml").unlink()
    assert _run(root, "manifest").stdout == "0.3.0\n"


def test_release_py_manifest_refuses_a_before_commit_with_no_version(
    tmp_path: Path,
) -> None:
    """``manifest`` exits nonzero and prints nothing when neither the moved nor the old apm.yml has a version."""
    root = _repo(tmp_path)
    (root / MANIFEST).unlink()

    res = _run(root, "manifest")

    assert res.returncode == 1
    assert res.stdout == ""
    assert "apm/apm.yml has no top-level version: line" in res.stderr


def test_release_py_manifest_falls_back_to_apm_yml_on_a_commit_before_the_move(
    tmp_path: Path,
) -> None:
    """On a commit from before ADR 0045, with apm/apm.yml and no packages/kmctl/apm, ``manifest`` reads apm/apm.yml.

    The first release after the move compares against such a commit.
    """
    root = _repo(tmp_path, version="0.12.2")
    shutil.move(root / MANIFEST.parent, root / "apm")
    _set_apm_version(root / "apm.yml", "0.11.0")
    assert (root / OLD_MANIFEST).is_file() and not (root / MANIFEST).exists()

    res = _run(root, "manifest")

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.12.2\n"
    _set_apm_version(root / OLD_MANIFEST, "0.12.1")
    assert _run(root, "manifest").stdout == "0.12.1\n"


def test_release_py_manifest_prefers_the_moved_apm_yml(tmp_path: Path) -> None:
    """With both files present, ``manifest`` reads packages/kmctl/apm/apm.yml, not apm/apm.yml."""
    root = _repo(tmp_path, version="0.13.0")
    (root / OLD_MANIFEST).parent.mkdir()
    shutil.copy(root / MANIFEST, root / OLD_MANIFEST)
    _set_apm_version(root / OLD_MANIFEST, "0.12.2")

    assert _run(root, "manifest").stdout == "0.13.0\n"


def test_release_py_set_moves_the_pins_from_an_older_tag(tmp_path: Path) -> None:
    """A second ``set`` replaces the older tag on every line instead of appending."""
    root = _repo(tmp_path)
    assert _run(root, "set", "0.2.0").returncode == 0

    res = _run(root, "set", "0.3.0rc1")

    assert res.returncode == 0, res.stderr
    assert _manifest_version(root) == "0.3.0rc1"
    assert _refs(root) == ["v0.3.0rc1"] * 6


def test_release_py_set_refuses_fewer_than_six_doc_lines(tmp_path: Path) -> None:
    """With an install line gone, ``set`` exits nonzero and writes nothing."""
    root = _repo(tmp_path)
    readme = root / "README.md"
    readme.write_text(INSTALL_RE.sub("", readme.read_text()))
    before = {rel: (root / rel).read_text() for rel in (MANIFEST, *DOC_FILES)}

    res = _run(root, "set", "0.2.0")

    assert res.returncode == 1
    assert "found 5 of the 6 install lines" in res.stderr
    assert {rel: (root / rel).read_text() for rel in before} == before


@pytest.mark.parametrize(
    ("version", "needle"),
    [
        ("0.2", "X.Y.Z"),
        ("0.2.0-rc1", "canonical"),
        ("banana", "not a version"),
        ("0.2.0.dev3", "not a release"),
        ("0.2.0+local", "not a release"),
    ],
)
def test_release_py_set_refuses_an_invalid_version(
    tmp_path: Path, version: str, needle: str
) -> None:
    """A malformed or unreleasable version exits nonzero and changes no file."""
    root = _repo(tmp_path)

    res = _run(root, "set", version)

    assert res.returncode == 1
    assert needle in res.stderr
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout == ""


@pytest.mark.parametrize(
    ("old", "new", "verdict"),
    [
        ("0.1.0", "0.2.0", "raised"),
        ("0.2.0a1", "0.2.0", "raised"),
        ("", "0.2.0", "raised"),
        ("0.2.0", "0.2.0", "same"),
        ("0.2.0", "0.1.9", "lowered"),
        ("0.2.0", "0.3.0.dev1", "skip"),
        ("0.2.0", "0.3.0+abc", "skip"),
        ("", "0.2.0.dev0", "skip"),
    ],
)
def test_release_py_compare(tmp_path: Path, old: str, new: str, verdict: str) -> None:
    """``compare OLD NEW`` says whether a push raised, kept or lowered the version."""
    res = _run(_repo(tmp_path), "compare", old, new)

    assert res.returncode == 0, res.stderr
    assert res.stdout == f"{verdict}\n"


@pytest.mark.parametrize(
    ("version", "code"),
    [("0.2.0a1", 0), ("0.2.0b2", 0), ("0.2.0rc1", 0), ("0.2.0", 1)],
)
def test_release_py_is_prerelease(tmp_path: Path, version: str, code: int) -> None:
    """``is-prerelease`` exits 0 for an a, b or rc version and 1 for a release."""
    assert _run(_repo(tmp_path), "is-prerelease", version).returncode == code


def test_release_py_set_never_commits_or_tags(tmp_path: Path) -> None:
    """``set`` leaves HEAD, the branches and the tags as they were."""
    root = _repo(tmp_path)

    def refs() -> str:
        return subprocess.run(
            ["git", "show-ref"], cwd=root, capture_output=True, text=True, check=True
        ).stdout

    before = refs()

    assert _run(root, "set", "0.2.0").returncode == 0

    assert refs() == before
    assert (
        subprocess.run(
            ["git", "tag"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        == ""
    )


def _hook_refs(root: Path) -> list[str]:
    """The refs the install hints in the Claude hook's hooks.json name."""
    text = (root / HOOKS).read_text()
    return re.findall(
        r"git\+https://github\.com/JasperHG90/kmctl@(v[0-9a-z.]+?)"
        r"(?:#subdirectory=packages/kmctl)?\.?'",
        text,
    )


def test_release_py_set_rewrites_the_hooks_json_ref(tmp_path: Path) -> None:
    """``set`` points both install hints in the Claude hook at the new tag, and a second ``set`` moves them."""
    root = _repo(tmp_path)

    assert _run(root, "set", "0.2.0").returncode == 0
    assert _hook_refs(root) == ["v0.2.0"] * 2
    res = _run(root, "set", "0.3.0rc1")

    assert res.returncode == 0, res.stderr
    assert _hook_refs(root) == ["v0.3.0rc1"] * 2
    assert f"wrote {HOOKS}" in res.stdout.splitlines()


def test_release_py_set_keeps_the_install_subdirectory(tmp_path: Path) -> None:
    """Each install line and hook hint ``set`` pins builds from packages/kmctl, once, after one set or two."""
    root = _repo(tmp_path)
    for rel in (*DOC_FILES, APM_DOC, HOOKS):
        # A line without the fragment, as before the move, gains it.
        path = root / rel
        path.write_text(path.read_text().replace(SUBDIRECTORY, ""))

    for version in ("0.13.0", "0.14.0rc1"):
        assert _run(root, "set", version).returncode == 0
        installs = [
            m
            for rel in (*DOC_FILES, APM_DOC)
            for m in INSTALL_RE.finditer((root / rel).read_text())
        ]
        assert len(installs) == 4
        for m in installs:
            assert (m.group(1), m.group(2)) == (f"@v{version}", SUBDIRECTORY)
        assert _hook_refs(root) == [f"v{version}"] * 2
        hooks = (root / HOOKS).read_text()
        assert hooks.count(f"@v{version}{SUBDIRECTORY}") == 2
        assert SUBDIRECTORY * 2 not in hooks


@pytest.mark.parametrize("version", ["0.12.2", "0.12.2rc1", "0.12.1"])
def test_release_py_set_at_or_below_the_cutoff_writes_no_subdirectory(
    tmp_path: Path, version: str
) -> None:
    """A release up to v0.12.2 built from the root, so set writes no fragment, and removes one it finds (subdirectory)."""
    root = _repo(tmp_path)
    assert _run(root, "set", "0.13.0").returncode == 0

    assert _run(root, "set", version).returncode == 0

    installs = [
        m
        for rel in (*DOC_FILES, APM_DOC)
        for m in INSTALL_RE.finditer((root / rel).read_text())
    ]
    assert len(installs) == 4
    for m in installs:
        assert (m.group(1), m.group(2)) == (f"@v{version}", None)
    hooks = (root / HOOKS).read_text()
    assert SUBDIRECTORY not in hooks
    assert hooks.count(f"@v{version}") == 2


def test_release_py_cutoff_is_plugin_s() -> None:
    """release.py and kmctl.plugin name the same last root release (cutoff)."""
    from kmctl.plugin import LAST_ROOT_RELEASE as plugin_cutoff
    from scripts.release import LAST_ROOT_RELEASE

    assert LAST_ROOT_RELEASE == plugin_cutoff


def _kmctl_ref_default(root: Path) -> str:
    """The default of copier.yml's kmctl_ref question at ``root``."""
    return str(yaml.safe_load((root / COPIER).read_text())["kmctl_ref"]["default"])


def test_release_py_set_moves_the_copier_default(tmp_path: Path) -> None:
    """``set`` writes kmctl_ref's default as the release tag and changes no other copier.yml line."""
    root = _repo(tmp_path)
    old = _kmctl_ref_default(root)

    res = _run(root, "set", "0.7.0rc1")

    assert res.returncode == 0, res.stderr
    assert _kmctl_ref_default(root) == "v0.7.0rc1"
    changed = set((root / COPIER).read_text().splitlines()) ^ set(
        (ROOT / COPIER).read_text().splitlines()
    )
    assert changed == {f"  default: {old}", "  default: v0.7.0rc1"}
    assert f"wrote {COPIER}" in res.stdout.splitlines()


def test_release_py_set_refuses_a_copier_yml_without_the_default(
    tmp_path: Path,
) -> None:
    """With no kmctl_ref default in copier.yml, ``set`` names copier.yml and writes no file."""
    root = _repo(tmp_path)
    copier = root / COPIER
    copier.write_text(
        "\n".join(
            line
            for line in copier.read_text().splitlines()
            if line != f"  default: {_kmctl_ref_default(ROOT)}"
        )
        + "\n"
    )
    subprocess.run([*GIT, "commit", "-qam", "drop the default"], cwd=root, check=True)

    res = _run(root, "set", "0.7.0")

    assert res.returncode == 1
    assert "copier.yml has no kmctl_ref question with a default: line" in res.stderr
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    assert status.stdout == ""


#: kmaudit's package, whose pyproject reads the version from its apm/apm.yml.
KMAUDIT = Path("packages/kmaudit")
#: kmaudit's commands reference, whose tracing install line kmaudit set pins.
KMAUDIT_DOCS = KMAUDIT / "docs" / "commands.md"
#: The git URL kmaudit's MCP server is installed from, before its ``@ref``.
KMAUDIT_SERVER = "git+https://github.com/JasperHG90/kmctl"


def _kmaudit_server_ref(root: Path) -> str:
    """The ref the kmaudit MCP server in ``root``'s kmaudit apm.yml installs from."""
    data = yaml.safe_load((root / KMAUDIT_MANIFEST).read_text())
    [server] = [s for s in data["dependencies"]["mcp"] if s["name"] == "kmaudit"]
    [source] = [a for a in server["args"] if a.startswith(KMAUDIT_SERVER)]
    return source.removeprefix(f"{KMAUDIT_SERVER}@").split("#")[0]


def test_kmaudit_version_source_is_its_apm_package() -> None:
    """kmaudit's pyproject sets no fixed version; hatchling's regex source reads its apm/apm.yml, as kmctl's does."""
    data = tomllib.loads((ROOT / KMAUDIT / "pyproject.toml").read_text())

    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    source = data["tool"]["hatch"]["version"]
    assert source["source"] == "regex"
    assert source["path"] == "apm/apm.yml"
    assert KMAUDIT / source["path"] == KMAUDIT_MANIFEST
    kmctl = tomllib.loads((ROOT / KMCTL / "pyproject.toml").read_text())
    assert source["pattern"] == kmctl["tool"]["hatch"]["version"]["pattern"]
    # A local uv run rebuilds kmaudit when the file changes.
    assert {"file": "apm/apm.yml"} in data["tool"]["uv"]["cache-keys"]
    assert not (ROOT / KMAUDIT / "VERSION").exists()


def test_kmaudit_version_is_not_copied_into_the_lock() -> None:
    """uv.lock holds no version for kmaudit, so a bump never has to re-lock."""
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    [entry] = [p for p in lock["package"] if p["name"] == "kmaudit"]

    assert "version" not in entry


def test_kmaudit_version_starts_unreleasable(tmp_path: Path) -> None:
    """kmaudit's apm.yml starts at 0.1.0.dev0, which compare skips, so the push adding it releases nothing."""
    assert _apm_version(ROOT / KMAUDIT_MANIFEST) == "0.1.0.dev0"

    current = _run(ROOT, "--package", "kmaudit", "current")
    verdict = _run(ROOT, "compare", "", "0.1.0.dev0")

    assert current.returncode == 0, current.stderr
    assert current.stdout == "0.1.0.dev0\n"
    assert verdict.stdout == "skip\n"


def test_kmaudit_version_builds_the_file_s_version(tmp_path: Path) -> None:
    """A copy of kmaudit's package with its apm.yml at 9.8.7 builds 9.8.7, and current prints it."""
    project = tmp_path / "project"
    shutil.copytree(
        ROOT / KMAUDIT,
        project / KMAUDIT,
        ignore=shutil.ignore_patterns("__pycache__", "tests", "docs"),
    )
    _set_apm_version(project / KMAUDIT_MANIFEST, "9.8.7")

    names = _build(project / KMAUDIT, tmp_path / "dist")

    assert names == ["kmaudit-9.8.7-py3-none-any.whl", "kmaudit-9.8.7.tar.gz"]
    assert _run(project, "--package", "kmaudit", "current").stdout == "9.8.7\n"


def _kmaudit_repo(tmp_path: Path) -> Path:
    """``_repo`` plus kmaudit's two apm.yml files, README and commands reference, committed."""
    root = _repo(tmp_path)
    for rel in (KMAUDIT_MANIFEST, KMAUDIT_CLAUDE, KMAUDIT / "README.md", KMAUDIT_DOCS):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, root / rel)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-q", "-m", "kmaudit"], cwd=root, check=True)
    return root


def _changed(root: Path) -> set[str]:
    """The paths ``git status`` shows as changed under ``root``."""
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line[3:] for line in status.stdout.splitlines()}


def test_package_aware_kmaudit_set_writes_only_its_files(tmp_path: Path) -> None:
    """``--package kmaudit set`` writes its apm.yml files' version and pins the README's and docs/commands.md's install lines to kmaudit-vX.Y.Z."""
    root = _kmaudit_repo(tmp_path)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 0, res.stderr
    assert res.stdout.splitlines() == [
        f"wrote {KMAUDIT_MANIFEST}",
        f"wrote {KMAUDIT_CLAUDE}",
        f"wrote {KMAUDIT / 'README.md'}",
        f"wrote {KMAUDIT_DOCS}",
    ]
    assert _changed(root) == {
        KMAUDIT_MANIFEST.as_posix(),
        KMAUDIT_CLAUDE.as_posix(),
        (KMAUDIT / "README.md").as_posix(),
        KMAUDIT_DOCS.as_posix(),
    }
    assert (
        "uv tool install --force 'kmaudit[tracing] @ git+https://github.com/JasperHG90/kmctl"
        "@kmaudit-v0.2.0#subdirectory=packages/kmaudit'"
        in (root / KMAUDIT_DOCS).read_text()
    )
    before = (ROOT / KMAUDIT_MANIFEST).read_text().splitlines()
    after = (root / KMAUDIT_MANIFEST).read_text().splitlines()
    assert set(before) - set(after) == {
        "version: 0.1.0.dev0",
        f'        - "{KMAUDIT_SERVER}@kmaudit-v0.1.0#subdirectory=packages/kmaudit"',
    }
    assert set(after) - set(before) == {
        "version: 0.2.0",
        f'        - "{KMAUDIT_SERVER}@kmaudit-v0.2.0#subdirectory=packages/kmaudit"',
    }
    assert _kmaudit_server_ref(root) == "kmaudit-v0.2.0"
    claude = yaml.safe_load((root / KMAUDIT_CLAUDE).read_text())
    assert claude["version"] == "0.2.0"
    assert (
        "uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl"
        "@kmaudit-v0.2.0#subdirectory=packages/kmaudit'"
        in (root / KMAUDIT / "README.md").read_text()
    )
    assert _run(root, "--package", "kmaudit", "current").stdout == "0.2.0\n"
    assert _run(root, "current").stdout == "0.1.0\n"


def test_package_aware_kmaudit_set_moves_an_older_pin(tmp_path: Path) -> None:
    """A second kmaudit release moves the README pin and the MCP server's ref from the older kmaudit-v tag."""
    root = _kmaudit_repo(tmp_path)

    assert _run(root, "--package", "kmaudit", "set", "0.2.0").returncode == 0
    assert _run(root, "set", "0.3.0", "--package", "kmaudit").returncode == 0

    text = (root / KMAUDIT / "README.md").read_text()
    assert "@kmaudit-v0.3.0#subdirectory=packages/kmaudit'" in text
    assert "kmaudit-v0.2.0" not in text
    assert _kmaudit_server_ref(root) == "kmaudit-v0.3.0"
    assert "kmaudit-v0.2.0" not in (root / KMAUDIT_MANIFEST).read_text()


def test_kmaudit_server_ref_is_the_next_tag_while_unreleased() -> None:
    """At a .dev version, the server names the tag the coming release gets, which set then keeps."""
    from packaging.version import Version

    version = Version(_apm_version(ROOT / KMAUDIT_MANIFEST) or "")

    assert _kmaudit_server_ref(ROOT) == f"kmaudit-v{version.base_version}"


def test_package_aware_kmaudit_set_refuses_an_apm_yml_without_the_server(
    tmp_path: Path,
) -> None:
    """With no kmaudit MCP server to pin in its apm.yml, kmaudit set writes nothing and names the file."""
    root = _kmaudit_repo(tmp_path)
    manifest = root / KMAUDIT_MANIFEST
    manifest.write_text(manifest.read_text().replace(KMAUDIT_SERVER, "kmaudit"))
    subprocess.run([*GIT, "commit", "-qam", "drop"], cwd=root, check=True)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 1
    assert f"{KMAUDIT_MANIFEST} declares no kmaudit MCP server" in res.stderr
    assert _changed(root) == set()


@pytest.mark.parametrize("drop", ["file", "version"])
def test_package_aware_kmaudit_set_refuses_a_missing_claude_sub_package(
    tmp_path: Path, drop: str
) -> None:
    """With the claude sub-package's apm.yml gone or versionless, kmaudit set writes nothing and names it."""
    root = _kmaudit_repo(tmp_path)
    claude = root / KMAUDIT_CLAUDE
    if drop == "file":
        claude.unlink()
    else:
        claude.write_text(
            re.sub(r"^version: .*\n", "", claude.read_text(), flags=re.MULTILINE)
        )
    subprocess.run([*GIT, "commit", "-qam", "drop"], cwd=root, check=True)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 1
    assert (
        f"{KMAUDIT_CLAUDE} is missing or has no top-level version: line" in res.stderr
    )
    assert _changed(root) == set()


def test_package_aware_kmaudit_set_refuses_a_readme_without_the_install_line(
    tmp_path: Path,
) -> None:
    """With no install line to pin, ``--package kmaudit set`` writes nothing and names the file."""
    root = _kmaudit_repo(tmp_path)
    (root / KMAUDIT / "README.md").write_text("# kmaudit\n")
    subprocess.run([*GIT, "commit", "-qam", "drop"], cwd=root, check=True)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 1
    assert "README.md" in res.stderr
    assert _changed(root) == set()


def test_package_aware_kmaudit_set_refuses_docs_without_the_tracing_install_line(
    tmp_path: Path,
) -> None:
    """With the tracing install line gone from the commands reference, kmaudit set writes nothing (install hints)."""
    root = _kmaudit_repo(tmp_path)
    docs = root / KMAUDIT_DOCS
    docs.write_text(
        "\n".join(
            ln for ln in docs.read_text().splitlines() if "kmaudit[tracing] @" not in ln
        )
    )
    subprocess.run([*GIT, "commit", "-qam", "drop"], cwd=root, check=True)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 1
    assert "commands.md" in res.stderr
    assert _changed(root) == set()


def test_package_aware_kmctl_set_is_unchanged(tmp_path: Path) -> None:
    """``--package kmctl set`` writes what ``set`` always has, and never kmaudit's files."""
    root = _kmaudit_repo(tmp_path)

    res = _run(root, "--package", "kmctl", "set", "0.2.0")

    assert res.returncode == 0, res.stderr
    assert res.stdout.splitlines() == [
        f"wrote {p}" for p in (*APM_FILES, *DOC_FILES, APM_DOC, COPIER, HOOKS)
    ]
    assert _changed(root) == {
        p.as_posix() for p in (*APM_FILES, *DOC_FILES, APM_DOC, COPIER, HOOKS)
    }
    for args in (("current",), ("manifest",)):
        assert _run(root, "--package", "kmctl", *args).stdout == "0.2.0\n"
        assert _run(root, *args).stdout == "0.2.0\n"


@pytest.mark.parametrize(
    ("args", "tag"),
    [
        (("tag", "0.2.0"), "v0.2.0"),
        (("--package", "kmctl", "tag", "0.2.0rc1"), "v0.2.0rc1"),
        (("--package", "kmaudit", "tag", "0.2.0"), "kmaudit-v0.2.0"),
    ],
)
def test_package_aware_tag_names_the_family(
    tmp_path: Path, args: tuple[str, ...], tag: str
) -> None:
    """``tag VERSION`` prints the package's tag: vX.Y.Z for kmctl, kmaudit-vX.Y.Z for kmaudit."""
    res = _run(tmp_path, *args)

    assert res.returncode == 0, res.stderr
    assert res.stdout == f"{tag}\n"


def test_package_aware_tag_refuses_an_unreleasable_version(tmp_path: Path) -> None:
    """A .dev version has no tag."""
    res = _run(tmp_path, "--package", "kmaudit", "tag", "0.1.0.dev0")

    assert res.returncode == 1
    assert "0.1.0.dev0" in res.stderr


def test_package_aware_kmaudit_set_refuses_an_apm_yml_with_no_version(
    tmp_path: Path,
) -> None:
    """``--package kmaudit set`` writes nothing when kmaudit's apm.yml has no ``version:`` line."""
    root = _kmaudit_repo(tmp_path)
    manifest = root / KMAUDIT_MANIFEST
    manifest.write_text(
        re.sub(r"^version: .*\n", "", manifest.read_text(), flags=re.MULTILINE)
    )
    subprocess.run([*GIT, "commit", "-qam", "drop version"], cwd=root, check=True)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 1
    assert f"{KMAUDIT_MANIFEST} has no top-level version: line" in res.stderr
    assert _changed(root) == set()
    assert _run(root, "--package", "kmaudit", "manifest").returncode == 1
