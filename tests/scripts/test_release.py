"""The release version: one source in ``apm/apm.yml``, and ``scripts/release.py`` (ADR 0012).

``packages/kmctl/pyproject.toml`` reads the version from ``apm/apm.yml``, kmctl's APM package
(ADR 0014), so a build needs no git history. ``scripts/release.py`` reads, writes and
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

from scripts.release import APM_DOC, APM_FILES, COPIER, DOC_FILES, HOOKS, MANIFEST

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "release.py"
#: kmctl's package, whose pyproject reads the version two folders up (ADR 0044).
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
    """Return the version ``apm/apm.yml`` under ``root`` declares."""
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
    """kmctl's ``pyproject.toml`` sets no fixed version; hatchling's regex source reads apm/apm.yml."""
    data = tomllib.loads((ROOT / KMCTL / "pyproject.toml").read_text())
    manifest = f"../../{MANIFEST.as_posix()}"

    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    source = data["tool"]["hatch"]["version"]
    assert source["source"] == "regex"
    assert source["path"] == manifest
    # A local uv run rebuilds kmctl when the manifest changes.
    assert {"file": manifest} in data["tool"]["uv"]["cache-keys"]
    assert {"file": "pyproject.toml"} in data["tool"]["uv"]["cache-keys"]


def test_version_source_builds_the_manifest_version(tmp_path: Path) -> None:
    """``uv build`` of kmctl's package gives a wheel and sdist at apm/apm.yml's version."""
    version = _manifest_version(ROOT)

    names = _build(ROOT / KMCTL, tmp_path)

    assert names == [f"kmctl-{version}-py3-none-any.whl", f"kmctl-{version}.tar.gz"]


def test_version_source_follows_a_changed_manifest(tmp_path: Path) -> None:
    """A copy of the project with apm/apm.yml at another version builds that version."""
    project = tmp_path / "project"
    project.mkdir()
    for folder in (KMCTL, Path("apm")):
        shutil.copytree(
            ROOT / folder,
            project / folder,
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
    """``current`` prints apm/apm.yml's version and nothing else."""
    res = _run(_repo(tmp_path, version="0.2.0a1"), "current")

    assert res.returncode == 0, res.stderr
    assert res.stdout == "0.2.0a1\n"


def test_release_py_docs_start_with_six_install_lines() -> None:
    """The docs this repository ships hold the six lines `set` rewrites."""
    assert len(_refs(ROOT)) == 6


def test_release_py_set_writes_the_version_and_the_six_doc_lines(
    tmp_path: Path,
) -> None:
    """``set`` writes the version, keeps apm/apm.yml's other lines and pins each doc line.

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
        "apm/apm.yml": "0.2.0",
        "apm/claude/apm.yml": "0.2.0",
        "apm/antigravity/apm.yml": "0.2.0",
    }
    for rel, text in before.items():
        changed = set((root / rel).read_text().splitlines()) ^ set(text.splitlines())
        assert changed == {"version: 0.1.0", "version: 0.2.0"}, rel
    assert _run(root, "current").stdout == "0.2.0\n"


def test_release_py_current_refuses_a_differing_apm_version(tmp_path: Path) -> None:
    """``current`` exits nonzero when the root apm.yml's version differs from apm/apm.yml's."""
    root = _repo(tmp_path, version="0.2.0")
    _set_apm_version(root / "apm.yml", "0.1.9")

    res = _run(root, "current")

    assert res.returncode == 1
    assert res.stdout == ""
    assert "apm.yml has version 0.1.9 but apm/apm.yml has 0.2.0" in res.stderr
    assert "scripts/release.py set 0.2.0" in res.stderr


def test_release_py_current_refuses_a_missing_apm_version(tmp_path: Path) -> None:
    """``current`` exits nonzero when apm/apm.yml is gone or the root apm.yml is."""
    root = _repo(tmp_path)
    (root / "apm.yml").unlink()
    assert "apm.yml has version none" in _run(root, "current").stderr
    (root / "apm" / "apm.yml").unlink()

    res = _run(root, "current")

    assert res.returncode == 1
    assert "apm/apm.yml has no top-level version: line" in res.stderr


def test_release_py_manifest_reads_a_before_commit_whose_root_apm_yml_differs(
    tmp_path: Path,
) -> None:
    """``manifest`` prints apm/apm.yml's version even when the root apm.yml differs or is gone.

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
    """``manifest`` exits nonzero and prints nothing when apm/apm.yml has no version."""
    root = _repo(tmp_path)
    (root / MANIFEST).unlink()

    res = _run(root, "manifest")

    assert res.returncode == 1
    assert res.stdout == ""
    assert "apm/apm.yml has no top-level version: line" in res.stderr


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


#: kmaudit's package, whose pyproject reads the version from its VERSION file.
KMAUDIT = Path("packages/kmaudit")


def test_kmaudit_version_source_is_the_version_file() -> None:
    """kmaudit's pyproject sets no fixed version; hatchling's regex source reads VERSION."""
    data = tomllib.loads((ROOT / KMAUDIT / "pyproject.toml").read_text())

    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    source = data["tool"]["hatch"]["version"]
    assert source["source"] == "regex"
    assert source["path"] == "VERSION"
    # A local uv run rebuilds kmaudit when the file changes.
    assert {"file": "VERSION"} in data["tool"]["uv"]["cache-keys"]


def test_kmaudit_version_is_not_copied_into_the_lock() -> None:
    """uv.lock holds no version for kmaudit, so a bump never has to re-lock."""
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    [entry] = [p for p in lock["package"] if p["name"] == "kmaudit"]

    assert "version" not in entry


def test_kmaudit_version_starts_unreleasable(tmp_path: Path) -> None:
    """VERSION starts at 0.1.0.dev0, which compare skips, so the push adding it releases nothing."""
    assert (ROOT / KMAUDIT / "VERSION").read_text() == "0.1.0.dev0\n"

    current = _run(ROOT, "--package", "kmaudit", "current")
    verdict = _run(ROOT, "compare", "", "0.1.0.dev0")

    assert current.returncode == 0, current.stderr
    assert current.stdout == "0.1.0.dev0\n"
    assert verdict.stdout == "skip\n"


def test_kmaudit_version_builds_the_file_s_version(tmp_path: Path) -> None:
    """A copy of kmaudit's package with VERSION at 9.8.7 builds 9.8.7, and current prints it."""
    project = tmp_path / "project"
    shutil.copytree(
        ROOT / KMAUDIT,
        project / KMAUDIT,
        ignore=shutil.ignore_patterns("__pycache__", "tests", "docs"),
    )
    (project / KMAUDIT / "VERSION").write_text("9.8.7\n")

    names = _build(project / KMAUDIT, tmp_path / "dist")

    assert names == ["kmaudit-9.8.7-py3-none-any.whl", "kmaudit-9.8.7.tar.gz"]
    assert _run(project, "--package", "kmaudit", "current").stdout == "9.8.7\n"


def _kmaudit_repo(tmp_path: Path) -> Path:
    """``_repo`` plus kmaudit's VERSION file and README, committed."""
    root = _repo(tmp_path)
    for rel in (KMAUDIT / "VERSION", KMAUDIT / "README.md"):
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
    """``--package kmaudit set`` writes VERSION and pins the README install line to kmaudit-vX.Y.Z."""
    root = _kmaudit_repo(tmp_path)

    res = _run(root, "--package", "kmaudit", "set", "0.2.0")

    assert res.returncode == 0, res.stderr
    assert res.stdout.splitlines() == [
        f"wrote {KMAUDIT / 'VERSION'}",
        f"wrote {KMAUDIT / 'README.md'}",
    ]
    assert _changed(root) == {
        (KMAUDIT / "VERSION").as_posix(),
        (KMAUDIT / "README.md").as_posix(),
    }
    assert (root / KMAUDIT / "VERSION").read_text() == "0.2.0\n"
    assert (
        "uv tool install 'kmaudit @ git+https://github.com/JasperHG90/kmctl"
        "@kmaudit-v0.2.0#subdirectory=packages/kmaudit'"
        in (root / KMAUDIT / "README.md").read_text()
    )
    assert _run(root, "--package", "kmaudit", "current").stdout == "0.2.0\n"
    assert _run(root, "current").stdout == "0.1.0\n"


def test_package_aware_kmaudit_set_moves_an_older_pin(tmp_path: Path) -> None:
    """A second kmaudit release moves the README pin from the older kmaudit-v tag."""
    root = _kmaudit_repo(tmp_path)

    assert _run(root, "--package", "kmaudit", "set", "0.2.0").returncode == 0
    assert _run(root, "set", "0.3.0", "--package", "kmaudit").returncode == 0

    text = (root / KMAUDIT / "README.md").read_text()
    assert "@kmaudit-v0.3.0#subdirectory=packages/kmaudit'" in text
    assert "kmaudit-v0.2.0" not in text


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
