import json
import os
import shutil
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from kmctl import app, plugin
from kmctl.briefing import RULES, TOKEN_BUDGET, estimate_tokens


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    """A repository with a bundle, one concept due (unverified) and two live handoffs."""
    assert _invoke("init", "--path", str(root)).exit_code == 0
    for title in ("Earlier work", "Latest work"):
        result = _invoke(
            "new",
            "handoff",
            title,
            "--description",
            f"Where {title} stands.",
            "--path",
            str(root),
        )
        assert result.exit_code == 0, result.output
    return root


def _briefing(root: Path, *args: str) -> Result:
    return _invoke("briefing", "--path", str(root), *args)


def test_briefing_has_three_parts(tmp_path: Path) -> None:
    out = _briefing(_repo(tmp_path)).stdout

    assert "Knowledge in this repository" in out
    assert "Verbs:" in out
    assert "due for review" in out
    assert ".claude/rules/" in out
    assert "unverified-is-a-lead" in out


def test_briefing_state_counts(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    due = json.loads(_invoke("review", "due", "--path", str(root), "--json").stdout)[
        "due"
    ]
    live = json.loads(_invoke("handoffs", "--path", str(root), "--json").stdout)

    state = json.loads(_briefing(root, "--json").stdout)["state"]

    assert state["due"] == len(due)
    assert state["live_handoffs"] == len(live) == 2
    assert state["newest_handoff"] == live[0]["title"]
    assert "manifesto" not in json.dumps(state)


def test_briefing_token_budget(tmp_path: Path) -> None:
    out = _briefing(_repo(tmp_path)).stdout

    assert estimate_tokens(out) < TOKEN_BUDGET, estimate_tokens(out)


def test_briefing_rules_are_not_in_the_rule_files() -> None:
    """The briefing repeats no constraint the package's rules already put in .claude/rules/."""
    instructions = (
        Path(__file__).resolve().parents[1] / "apm" / "claude" / ".apm" / "instructions"
    )
    written = " ".join(
        " ".join(p.read_text().split()) for p in sorted(instructions.glob("*.md"))
    )
    assert written
    for name, text in RULES:
        assert f'name="{name}"' not in written, name
        assert text not in written, name


def test_briefing_empty_repository(tmp_path: Path) -> None:
    result = _briefing(tmp_path)

    assert result.exit_code == 0
    assert "kmctl init" in result.stdout


def test_briefing_writes_nothing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}

    _briefing(root)
    _briefing(root, "--json")

    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_briefing_json(tmp_path: Path) -> None:
    data = json.loads(_briefing(_repo(tmp_path), "--json").stdout)

    assert {"routing", "state", "rules"} <= data.keys()


def test_briefing_state_line_reads_right_for_one(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    # Verify init's first decision, so the manifesto is the one concept due.
    decision = (
        tmp_path / ".okf/decisions/0001-keep-project-knowledge-in-an-okf-bundle.md"
    )
    decision.write_text(
        decision.read_text().replace(
            "status: stable\n",
            "status: stable\nverified:\n  - by: human:test\n    at: 2026-10-15T00:00:00Z\n",
            1,
        )
    )
    _invoke(
        "new",
        "handoff",
        "Only one",
        "--description",
        "Where it stands.",
        "--path",
        str(tmp_path),
    )

    out = _briefing(tmp_path).stdout

    assert "1 concept due for review" in out
    assert "1 live handoff," in out


def _skill_names(skills_dir: Path) -> list[str]:
    return sorted(p.name for p in skills_dir.iterdir() if p.is_dir())


def test_briefing_names_every_skill(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    out = _briefing(_repo(root)).stdout
    names = _skill_names(plugin.skills_dir())

    assert names
    assert [n for n in names if f"- {n}:" not in out] == []


def test_briefing_skills_are_read_at_run_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy = tmp_path / "skills"
    shutil.copytree(plugin.skills_dir(), copy)
    extra = copy / "extra-skill"
    extra.mkdir()
    (extra / "SKILL.md").write_text(
        "---\nname: extra-skill\ndescription: Do one extra thing. Use when asked.\n---\n"
    )
    monkeypatch.setattr(plugin, "skills_dir", lambda: copy)
    root = tmp_path / "repo"
    root.mkdir()

    out = _briefing(_repo(root)).stdout

    assert "- extra-skill: Do one extra thing." in out
    assert [n for n in _skill_names(copy) if f"- {n}:" not in out] == []


def test_briefing_unchanged_by_the_seeded_files(tmp_path: Path) -> None:
    """The agent-file block and first decision init writes leave the briefing's text alone."""
    seeded, plain = tmp_path / "seeded", tmp_path / "plain"
    seeded.mkdir()
    assert _invoke("init", "--path", str(seeded)).exit_code == 0
    for rel in (
        "docs/README.md",
        ".okf/index.md",
        ".okf/log.md",
        ".okf/manifesto.md",
        ".okf/summary.md",
    ):
        (plain / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(seeded / rel, plain / rel)
    assert (seeded / "CLAUDE.md").is_file()

    with_seed = json.loads(_briefing(seeded, "--json").stdout)
    without = json.loads(_briefing(plain, "--json").stdout)

    for key in ("routing", "rules", "skills"):
        assert with_seed[key] == without[key], key
    assert [r["name"] for r in with_seed["rules"]] == ["unverified-is-a-lead"]


def test_briefing_setup_after_init_puts_the_scaffold_first(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0

    out = _briefing(tmp_path).stdout
    setup = json.loads(_briefing(tmp_path, "--json").stdout)["setup"]

    assert out.splitlines()[1] == (
        "Setup first: manifesto not written; no architecture pages. "
        "Ask the user to fill these in with you now."
    )
    assert setup == {
        "initialized": True,
        "manifesto_written": False,
        "architecture_detailed": False,
    }


def test_briefing_setup_done(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    manifesto = tmp_path / ".okf/manifesto.md"
    manifesto.write_text(
        manifesto.read_text().replace(
            "## What this is for\n", "## What this is for\n\nA test repository.\n"
        )
    )
    architecture = tmp_path / ".okf/architecture"
    architecture.mkdir()
    (architecture / "index.md").write_text("# Architecture\n")
    assert "no architecture pages" in _briefing(tmp_path).stdout
    (architecture / "overview.md").write_text("# Overview\n")

    out = _briefing(tmp_path).stdout

    assert out.splitlines()[1] == (
        "Setup: kmctl initialized, manifesto written, architecture detailed."
    )


def test_briefing_setup_without_init(tmp_path: Path) -> None:
    out = _briefing(tmp_path).stdout
    setup = json.loads(_briefing(tmp_path, "--json").stdout)["setup"]

    assert out.splitlines()[1] == (
        "Setup first: kmctl is not initialized. Ask the user to run kmctl "
        "init, then write the manifesto and architecture with you."
    )
    assert not any(setup.values())


def test_briefing_setup_without_a_manifesto(tmp_path: Path) -> None:
    (tmp_path / ".okf").mkdir()

    assert "manifesto not written" in _briefing(tmp_path).stdout


def test_briefing_setup_reads_crlf_front_matter(tmp_path: Path) -> None:
    assert _invoke("init", "--path", str(tmp_path)).exit_code == 0
    manifesto = tmp_path / ".okf/manifesto.md"
    manifesto.write_bytes(manifesto.read_bytes().replace(b"\n", b"\r\n"))

    assert "manifesto not written" in _briefing(tmp_path).stdout


def test_briefing_long_handoff_title_keeps_the_budget(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    title = " ".join(["ab"] * 40)
    result = _invoke(
        "new", "handoff", title, "--description", "x.", "--path", str(root)
    )
    assert result.exit_code == 0, result.output

    out = _briefing(root).stdout

    assert estimate_tokens(out) < TOKEN_BUDGET, estimate_tokens(out)
    assert title not in out


# The summary: where to start, and whether it is current (ADR 0027) ---------------


def _git(root: Path, *args: str) -> None:
    env = os.environ | {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def _git_repo(root: Path) -> Path:
    """``_repo`` as a git repository with everything committed."""
    _git(root, "init", "-q", "-b", "main")
    _repo(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    return root


def _state_line(out: str) -> str:
    return next(line for line in out.splitlines() if line.startswith("State: "))


def test_briefing_starts_at_the_summary(tmp_path: Path) -> None:
    out = " ".join(_briefing(_repo(tmp_path)).stdout.split())

    assert "Start at .okf/summary.md." in out
    assert ".okf/index.md" not in out


def test_briefing_without_a_summary_starts_at_the_index(tmp_path: Path) -> None:
    """A bundle that never ran kmctl update has no summary: the briefing names the index."""
    root = _repo(tmp_path)
    (root / ".okf" / "summary.md").unlink()

    out = " ".join(_briefing(root).stdout.split())
    routing = json.loads(_briefing(root, "--json").stdout)["routing"]

    assert "Start at .okf/index.md." in out
    assert "summary.md" not in out and "summary.md" not in routing


def test_briefing_summary_current_then_behind(tmp_path: Path) -> None:
    root = _git_repo(tmp_path)
    assert _state_line(_briefing(root).stdout).endswith("; summary current.")
    assert json.loads(_briefing(root, "--json").stdout)["state"]["summary_behind"] == 0

    _invoke("new", "decision", "One", "--description", "One.", "--path", str(root))
    one = _state_line(_briefing(root).stdout)
    _invoke("new", "practice", "Two", "--description", "Two.", "--path", str(root))
    two = _state_line(_briefing(root).stdout)

    assert one.endswith("; summary behind: 1 concept changed.")
    assert two.endswith("; summary behind: 2 concepts changed.")
    assert json.loads(_briefing(root, "--json").stdout)["state"]["summary_behind"] == 2


def test_briefing_summary_state_left_out_without_git(tmp_path: Path) -> None:
    out = _briefing(_repo(tmp_path)).stdout

    assert "summary current" not in out and "summary behind" not in out
    assert (
        json.loads(_briefing(tmp_path, "--json").stdout)["state"]["summary_behind"]
        is None
    )


def test_briefing_summary_behind_with_a_long_handoff_title_keeps_the_budget(
    tmp_path: Path,
) -> None:
    """The worst case: a clipped handoff title, and a summary 100 concepts behind."""
    root = _git_repo(tmp_path)
    title = " ".join(["ab"] * 40)
    result = _invoke(
        "new", "handoff", title, "--description", "x.", "--path", str(root)
    )
    assert result.exit_code == 0, result.output
    for n in range(100):
        made = _invoke(
            "new", "decision", f"D {n}", "--description", "x.", "--path", str(root)
        )
        assert made.exit_code == 0, made.output

    out = _briefing(root).stdout

    assert "; summary behind: 100 concepts changed." in out
    assert estimate_tokens(out) < TOKEN_BUDGET, estimate_tokens(out)
    assert title not in out


# The newer-release line and the not-installed notice (ADR 0026) -----------------

LATEST = "v99.0.0"
LINE = f"kmctl {LATEST} is out; this project pins"


@pytest.fixture
def update_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The copy on PATH (KMCTL_PINNED unset) with a fresh cache naming LATEST; returns the cache file."""
    from kmctl import pin

    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.delenv("KMCTL_NO_UPDATE_CHECK", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    cache = pin.cache_file()
    cache.parent.mkdir(parents=True)
    cache.write_text(LATEST + "\n")
    started: list[object] = []
    monkeypatch.setattr(pin, "start_refresh", lambda: started.append(1))
    return cache


def _pinned_repo(tmp_path: Path, ref: str) -> Path:
    """A git repository whose lock pins kmctl at ``ref``."""
    from test_pin import write_lock

    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    write_lock(root, ref=ref)
    return root


def _own() -> str:
    """This kmctl's own tag."""
    return plugin.package_ref()


def test_briefing_newer_release_line_in_text(
    tmp_path: Path, update_check: Path
) -> None:
    out = _briefing(_pinned_repo(tmp_path, _own())).stdout

    assert out.rstrip("\n").splitlines()[-1] == (
        f"{LINE} {_own()}. Tell the user; `just upgrade {LATEST}` moves it."
    )
    assert out.count(LINE) == 1


def test_briefing_newer_release_key_in_json(tmp_path: Path, update_check: Path) -> None:
    data = json.loads(_briefing(_pinned_repo(tmp_path, _own()), "--json").stdout)

    assert data["newer_release"] == {"latest": LATEST, "pinned": _own()}


def test_briefing_newer_release_line_in_antigravity(
    tmp_path: Path, update_check: Path
) -> None:
    out = _briefing(_pinned_repo(tmp_path, _own()), "--format", "antigravity").stdout
    text = json.loads(out)["injectSteps"][0]["systemMessage"]["systemMessage"]

    assert text.splitlines()[-1].startswith(LINE)


def test_briefing_newer_release_line_for_a_pre_release_pin(
    tmp_path: Path, update_check: Path
) -> None:
    update_check.write_text("v0.6.0\n")

    out = _briefing(_pinned_repo(tmp_path, "v0.6.0rc1")).stdout

    assert "kmctl v0.6.0 is out; this project pins v0.6.0rc1." in out


@pytest.mark.parametrize("cached", ["same", "v0.0.1"])
def test_briefing_newer_release_none_when_not_newer(
    tmp_path: Path, update_check: Path, cached: str
) -> None:
    update_check.write_text((_own() if cached == "same" else cached) + "\n")

    out = _briefing(_pinned_repo(tmp_path, _own())).stdout

    assert "is out; this project pins" not in out


@pytest.mark.parametrize("env", ["KMCTL_NO_UPDATE_CHECK", "KMCTL_PINNED"])
def test_briefing_newer_release_none_when_turned_off(
    tmp_path: Path, update_check: Path, monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    monkeypatch.setenv(env, "1")

    out = _briefing(_pinned_repo(tmp_path, _own())).stdout

    assert "is out; this project pins" not in out


def test_briefing_newer_release_none_without_a_lock(
    tmp_path: Path, update_check: Path
) -> None:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)

    assert "is out; this project pins" not in _briefing(root).stdout


@pytest.mark.parametrize(
    ("args", "child"),
    [
        ((), "kmctl briefing (kmctl 0.5.1)\nold text\n"),
        (("--json",), json.dumps({"routing": "old"}) + "\n"),
        (
            ("--format", "antigravity"),
            json.dumps({"injectSteps": [{"systemMessage": {"systemMessage": "old"}}]})
            + "\n",
        ),
    ],
)
def test_briefing_newer_release_over_a_handed_off_old_release(
    tmp_path: Path,
    update_check: Path,
    monkeypatch: pytest.MonkeyPatch,
    args: tuple[str, ...],
    child: str,
) -> None:
    """The copy on PATH adds the line once over an old pinned release's own briefing."""
    from test_pin import FAKE_UVX, kmctl

    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "uvx").write_text(FAKE_UVX.format(python=sys.executable))
    (bin_dir / "uvx").chmod(0o755)
    monkeypatch.setenv("FAKE_UVX_LOG", str(tmp_path / "uvx.log"))
    monkeypatch.setenv("FAKE_UVX_OUT", child)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    root = _pinned_repo(tmp_path, "v0.5.1")

    res = kmctl(root, "briefing", *args)

    assert res.returncode == 0, res.stderr
    assert res.stdout.count(LINE) == (0 if args == ("--json",) else 1)
    if args:
        data = json.loads(res.stdout)
        if args == ("--json",):
            assert data["routing"] == "old"
            assert data["newer_release"] == {"latest": LATEST, "pinned": "v0.5.1"}
        else:
            text = data["injectSteps"][0]["systemMessage"]["systemMessage"]
            assert text.startswith("old\n")
    else:
        assert res.stdout.startswith("kmctl briefing (kmctl 0.5.1)\nold text\n")


def test_briefing_newer_release_and_not_installed_when_the_pin_is_not_cached(
    tmp_path: Path, update_check: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The offline probe misses: the copy on PATH briefs and says to run just install."""
    from test_pin import FAKE_UVX, kmctl

    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "uvx").write_text(FAKE_UVX.format(python=sys.executable))
    (bin_dir / "uvx").chmod(0o755)
    monkeypatch.setenv("FAKE_UVX_LOG", str(tmp_path / "uvx.log"))
    monkeypatch.setenv("FAKE_UVX_MISS", "1")
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    root = _pinned_repo(tmp_path, "v0.5.1")

    res = kmctl(root, "briefing")

    assert res.returncode == 0, res.stderr
    assert f"kmctl briefing (kmctl {version('kmctl')})" in res.stdout
    assert "This project pins kmctl v0.5.1, which is not installed yet" in res.stdout
    assert "`just install`" in res.stdout
    assert res.stdout.count(LINE) == 1


# The refresh of the newest release -----------------------------------------------


def _record_popen(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], dict]]:
    """Record pin's Popen calls instead of starting a process."""
    from kmctl import pin

    started: list[tuple[list[str], dict]] = []

    def fake(cmd: list[str], **kwargs: object) -> None:
        started.append((cmd, kwargs))

    monkeypatch.setattr(pin.subprocess, "Popen", fake)
    return started


@pytest.mark.parametrize("cache", ["missing", "stale"])
def test_briefing_refresh_starts_detached_when_the_cache_is_old(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, cache: str
) -> None:
    import subprocess as sp

    from kmctl import pin

    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    if cache == "stale":
        path = pin.cache_file()
        path.parent.mkdir(parents=True)
        path.write_text(LATEST + "\n")
        old = time.time() - pin.CACHE_SECONDS - 60
        os.utime(path, (old, old))
    started = _record_popen(monkeypatch)

    _briefing(_pinned_repo(tmp_path, _own()))

    [(cmd, kwargs)] = started
    assert cmd[1:] == ["-m", "kmctl.pin"]
    assert kwargs["start_new_session"] is True
    for stream in ("stdin", "stdout", "stderr"):
        assert kwargs[stream] is sp.DEVNULL


def test_briefing_refresh_not_started_when_the_cache_is_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from kmctl import pin

    monkeypatch.delenv("KMCTL_PINNED")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    pin.cache_file().parent.mkdir(parents=True)
    pin.cache_file().write_text(LATEST + "\n")
    started = _record_popen(monkeypatch)

    _briefing(_pinned_repo(tmp_path, _own()))

    assert started == []


FAKE_GIT = """#!/bin/sh
{body}
"""
LS_REMOTE = (
    "aaa\trefs/tags/v0.5.1\n"
    "bbb\trefs/tags/v0.10.0\n"
    "ccc\trefs/tags/v0.9.2\n"
    "ddd\trefs/tags/v0.11.0rc1\n"
    "eee\trefs/tags/not-a-version\n"
)


def _fake_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> None:
    """Put a git first on PATH that runs the shell ``body``."""
    bin_dir = tmp_path / "gitbin"
    bin_dir.mkdir()
    (bin_dir / "git").write_text(FAKE_GIT.format(body=body))
    (bin_dir / "git").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))


def test_briefing_refresh_writes_the_newest_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The newest of v0.5.1, v0.10.0 and v0.9.2, skipping v0.11.0rc1."""
    from kmctl import pin

    listing = tmp_path / "ls-remote.txt"
    listing.write_text(LS_REMOTE)
    _fake_git(tmp_path, monkeypatch, f'cat "{listing}"')

    pin.refresh()

    assert pin.cache_file().read_text() == "v0.10.0\n"


@pytest.mark.parametrize("body", ["exit 128", "sleep 5"])
def test_briefing_refresh_leaves_the_cache_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str
) -> None:
    """A failing or slow git leaves the cache as it was and raises nothing."""
    from kmctl import pin

    _fake_git(tmp_path, monkeypatch, body)
    monkeypatch.setattr(pin, "REFRESH_TIMEOUT_SECONDS", 0.5)
    pin.cache_file().parent.mkdir(parents=True)
    pin.cache_file().write_text("v0.1.0\n")

    pin.refresh()

    assert pin.cache_file().read_text() == "v0.1.0\n"
