"""The starter template: copier.yml at the root, its files in starter/ (ADR 0025).

The default tier renders the template from a copy of this tree with copier,
as ``uvx copier copy gh:JasperHG90/kmctl`` does from a release tag. The
``integration`` test bootstraps a generated project with git rewriting
GitHub's kmctl URL to a ``file://`` clone of this tree, so the CLI and the
package it installs are this checkout's.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
import yaml
from conftest import tree_repo
from jsonschema import Draft202012Validator

from kmctl.kinds import schema
from kmctl.okf import front_matter

ROOT = Path(__file__).resolve().parents[1]
TAG = f"v{version('kmctl')}"
KMCTL_GIT = "https://github.com/JasperHG90/kmctl.git"
HARNESS_SETS = (
    "[claude]",
    "[antigravity]",
    "[opencode]",
    "[claude, antigravity]",
    "[claude, antigravity, opencode]",
)
# What a generated project holds: the template's files, rendered.
GENERATED = {
    ".copier-answers.yml",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
    ".gitignore",
    ".pre-commit-config.yaml",
    "AGENTS.md",
    "README.md",
    "apm.yml",
    "justfile",
}
# Doctor checks a runner cannot pass: no harness CLI, and nobody trusts the
# folder in Antigravity.
UNPASSABLE = {"dep.claude", "dep.agy", "dep.opencode", "antigravity.trust"}
# Found before the consumer fixture narrows PATH.
JUST = shutil.which("just")
HOW_TO = ROOT / "docs" / "how-to" / "start-a-repository-with-kmctl-starter.md"
DECISIONS = ROOT / ".okf" / "decisions"


@pytest.fixture(scope="module")
def template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A git repository holding this tree, tagged at kmctl's version, as copier's source."""
    return tree_repo(tmp_path_factory.mktemp("template") / "kmctl")


def _copier(src: Path, dst: Path, *data: str) -> subprocess.CompletedProcess[str]:
    """Run ``copier copy --defaults`` from ``src``'s HEAD into ``dst`` with each ``KEY=VALUE``.

    ``src`` goes as a git+file:// URL: git then packs the objects it sends, where a
    plain path makes it copy object files one by one.
    """
    args = [arg for pair in data for arg in ("--data", pair)]
    return subprocess.run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--vcs-ref", "HEAD"]
        + ["--data", "project_name=demo", "--data", "codeowners=@octocat", *args]
        + ["git+" + src.as_uri(), str(dst)],
        capture_output=True,
        text=True,
        check=False,
    )


def _files(root: Path) -> set[str]:
    """Every file under ``root``, relative to it, outside .git."""
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


# r1: rendering ------------------------------------------------------------------


@pytest.mark.parametrize("harnesses", HARNESS_SETS)
def test_render_writes_the_project_pinned_to_this_release(
    template: Path, tmp_path: Path, harnesses: str
) -> None:
    """Each harness set renders the template's files, with targets and every pin at this release."""
    out = tmp_path / "demo"

    res = _copier(template, out, f"harnesses={harnesses}")

    assert res.returncode == 0, res.stderr
    assert _files(out) == GENERATED
    apm = yaml.safe_load((out / "apm.yml").read_text())
    assert apm["targets"] == yaml.safe_load(harnesses)
    assert apm["dependencies"]["apm"] == [{"git": KMCTL_GIT, "path": "apm", "ref": TAG}]
    assert f'kmctl_ref := "{TAG}"' in (out / "justfile").read_text()
    ci = yaml.safe_load((out / ".github" / "workflows" / "ci.yml").read_text())
    assert {"uses": f"JasperHG90/kmctl@{TAG}"} in ci["jobs"]["knowledge"]["steps"]
    yaml.safe_load((out / ".pre-commit-config.yaml").read_text())


# r2: the default is this release ------------------------------------------------


def test_render_default_is_this_release() -> None:
    """copier.yml's kmctl_ref default is the tag of the version apm/apm.yml holds."""
    manifest = yaml.safe_load((ROOT / "apm" / "apm.yml").read_text())
    questions = yaml.safe_load((ROOT / "copier.yml").read_text())

    assert questions["kmctl_ref"]["default"] == f"v{manifest['version']}"


# r3: the validator --------------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "refusal"),
    [
        (("kmctl_ref=main",), "not a branch"),
        (
            ("harnesses=[opencode]", "kmctl_ref=v0.5.0"),
            "OpenCode needs kmctl v0.5.1 or later",
        ),
    ],
)
def test_render_validator_refuses(
    template: Path, tmp_path: Path, data: tuple[str, ...], refusal: str
) -> None:
    """A branch, or OpenCode on a tag before v0.5.1, is refused with the reason."""
    res = _copier(template, tmp_path / "demo", *data)

    assert res.returncode != 0
    assert refusal in res.stdout + res.stderr
    assert not (tmp_path / "demo" / "apm.yml").exists()


@pytest.mark.parametrize(
    "data",
    [("harnesses=[claude]", "kmctl_ref=v0.5.0"), ("kmctl_ref=v0.6.0rc1",)],
)
def test_render_validator_takes_older_and_pre_release_tags(
    template: Path, tmp_path: Path, data: tuple[str, ...]
) -> None:
    """[claude] on v0.5.0 renders, and so does a pre-release tag such as release.py set writes."""
    out = tmp_path / "demo"

    res = _copier(template, out, *data)

    assert res.returncode == 0, res.stderr
    [entry] = yaml.safe_load((out / "apm.yml").read_text())["dependencies"]["apm"]
    assert entry["ref"] == data[-1].split("=", 1)[1]


# r6: a bootstrap from this checkout ----------------------------------------------


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` in ``cwd``, failing the test with its output when it fails."""
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"{cmd}\n{res.stdout}\n{res.stderr}"
    return res


@pytest.mark.integration
def test_bootstrap_installs_this_checkout(
    consumer: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """just bootstrap in a generated project installs this tree's kmctl and package, and its checks pass."""
    work = tree_repo(tmp_path / "kmctl")
    commit = _run(["git", "rev-parse", "HEAD"], work).stdout.strip()
    bare = tmp_path / "srv" / "kmctl.git"
    _run(["git", "clone", "-q", "--bare", str(work), str(bare)], tmp_path)
    # APM refuses a rewrite to http:// or another host, but follows one to
    # file:// (spike:starter-in-repo/5). The justfile names the URL without
    # .git and apm.yml with it; git takes the longest match.
    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text(
        f'[url "file://{bare}"]\n'
        f"\tinsteadOf = {KMCTL_GIT}\n"
        f"\tinsteadOf = {KMCTL_GIT.removesuffix('.git')}\n"
        "[user]\n\temail = t@e.invalid\n\tname = t\n"
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    for token in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_APM_PAT", "GITHUB_COPILOT_PAT"):
        monkeypatch.delenv(token, raising=False)
    assert JUST, "just must be on PATH"
    (tmp_path / "tools" / "just").symlink_to(JUST)
    bin_dir = Path(os.environ["HOME"]) / ".local" / "bin"
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    harnesses = "[claude, antigravity, opencode]"
    _run(
        [sys.executable, "-m", "copier", "copy", "--defaults", "--overwrite"]
        + ["--vcs-ref", "HEAD", "--data", "project_name=demo"]
        + ["--data", "codeowners=@octocat", "--data", f"harnesses={harnesses}"]
        + ["git+" + work.as_uri(), str(consumer)],
        tmp_path,
    )

    _run(["just", "bootstrap"], consumer)
    _run(["git", "add", "-A"], consumer)
    _run(["uvx", "prek@0.5.5", "run", "--all-files"], consumer)
    _run(["kmctl", "check"], consumer)
    report = json.loads(
        subprocess.run(
            ["kmctl", "doctor", "--json"],
            cwd=consumer,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    )

    failed = {c["id"] for c in report["checks"] if not c["ok"]}
    assert failed <= UNPASSABLE, report
    lock = yaml.safe_load((consumer / "apm.lock.yaml").read_text())
    [kmctl] = [d for d in lock["dependencies"] if d["name"] == "kmctl"]
    assert kmctl["resolved_commit"] == commit
    [receipt] = glob.glob(
        str(
            Path(os.environ["XDG_DATA_HOME"])
            / "uv/tools/kmctl/lib/python*/site-packages/kmctl-*.dist-info/direct_url.json"
        )
    )
    assert json.loads(Path(receipt).read_text())["vcs_info"]["commit_id"] == commit


# r8: the docs and the decision ----------------------------------------------------


def _flat(text: str) -> str:
    """``text`` with every run of whitespace made one space."""
    return " ".join(text.split())


def _decision() -> Path:
    """The decision that moved the template into kmctl."""
    [path] = list(DECISIONS.glob("0025-*.md"))
    return path


def test_docs_how_to_covers_the_starter() -> None:
    """The how-to gives the copy command, the questions, the files, upgrades and the move from kmctl-starter."""
    text = _flat(HOW_TO.read_text())

    for words in (
        "uvx copier copy gh:JasperHG90/kmctl my-project",
        "just bootstrap",
        "`kmctl_ref`",
        "`harnesses`",
        "apm.yml",
        "justfile",
        "just upgrade vX.Y.Z",
        "newest",
        "_src_path",
        "gh:JasperHG90/kmctl-starter",
        "_commit: v0.6.0",
        "--vcs-ref v0.3.0",
        "uvx copier update --defaults --skip-answered",
        "exclude:",
    ):
        assert words in text, words


def test_docs_readme_and_index_link_the_how_to() -> None:
    """README.md and the how-to index link the page."""
    link = "start-a-repository-with-kmctl-starter.md"

    assert f"docs/how-to/{link}" in (ROOT / "README.md").read_text()
    assert link in (ROOT / "docs" / "how-to" / "README.md").read_text()


def test_docs_name_the_old_repository_only_in_the_move_section() -> None:
    """No tracked file but the how-to's move section, and loop state, names gh:JasperHG90/kmctl-starter."""
    files = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    here = Path(__file__).relative_to(ROOT).as_posix()
    hits = [
        f
        for f in files
        if not f.startswith(".loop/")
        and f != here
        and (ROOT / f).is_file()
        and "gh:JasperHG90/kmctl-starter" in (ROOT / f).read_text(errors="replace")
    ]
    assert hits == [HOW_TO.relative_to(ROOT).as_posix()]
    sections = re.split(r"^## ", HOW_TO.read_text(), flags=re.MULTILINE)
    named = [s.splitlines()[0] for s in sections if "gh:JasperHG90/kmctl-starter" in s]
    assert named == ["Move a project made from kmctl-starter"]


def test_docs_decision_matches_the_decision_schema() -> None:
    """The decision's front matter matches kmctl's decision schema."""
    meta = json.loads(json.dumps(front_matter(_decision()), default=str))

    errors = [
        e.message for e in Draft202012Validator(schema("decision")).iter_errors(meta)
    ]

    assert errors == []


def test_docs_decision_records_why_and_the_costs() -> None:
    """The decision says why, the costs, and that older tags have no template."""
    text = _flat(_decision().read_text())

    for words in (
        "copier.yml",
        "starter/",
        "release tag",
        "scripts/release.py set",
        "kmctl_ref",
        "every kmctl release",
        "_src_path",
        "_commit: v0.6.0",
        "private",
        "no template",
        "file://",
    ):
        assert words in text, words
