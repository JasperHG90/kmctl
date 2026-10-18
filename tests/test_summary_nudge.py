"""kmctl summary nudge: the PostToolUse hook's ask to update .okf/summary.md or ack it.

Right after the agent changes a concept in .okf/, the nudge names the
concepts the summary is behind and both ways out. It decides with git only,
stays quiet for a set it already named, and prints ``{}`` on any failure.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from test_action import _kmctl_bin
from test_summary import _commit, _git, _init, _invoke, _new

from kmctl import antigravity, plugin
from kmctl.okf import field, front_matter

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "apm" / "claude" / ".apm" / "hooks" / "hooks.json"
SUMMARY = ".okf/summary.md"
ACK = "kmctl summary ack"
#: The pages that describe kmctl's hooks for people and agents.
PAGES = (
    "docs/explanation/why-one-hook-and-report-only-audits.md",
    "docs/reference/commands.md",
    ".okf/architecture/overview.md",
)


def _payload(cwd: Path | None, command: str = "kmctl new decision X") -> str:
    """A Claude Code PostToolUse payload for a Bash call, as spike:okf-summary-nudge/2 recorded it."""
    data: dict[str, object] = {
        "session_id": "s",
        "transcript_path": "/tmp/t.jsonl",
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {"stdout": "", "stderr": ""},
    }
    if cwd is not None:
        data["cwd"] = str(cwd)
    return json.dumps(data)


def _nudge(stdin: str, *args: str, fmt: str = "claude") -> tuple[int, str]:
    """Run kmctl summary nudge with ``stdin``; return its exit code and stdout."""
    from typer.testing import CliRunner

    from kmctl import app

    result = CliRunner().invoke(
        app, ["summary", "nudge", "--format", fmt, *args], input=stdin
    )
    return result.exit_code, result.stdout


def _context(out: str) -> str | None:
    """The additionalContext of a claude-format nudge, or None for ``{}``."""
    data = json.loads(out)
    if data == {}:
        return None
    assert data["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    return data["hookSpecificOutput"]["additionalContext"]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed repository set up by kmctl init, so its summary is current."""
    (tmp_path / "r").mkdir()
    return _init(tmp_path / "r")


# r1: it nudges ---------------------------------------------------------------------


def test_nudges_after_kmctl_new_decision_naming_it_and_both_ways_out(
    repo: Path,
) -> None:
    cid = _new(repo, "decision", "Use a nudge")

    code, out = _nudge(_payload(repo))

    assert code == 0
    data = json.loads(out)
    assert set(data) == {"hookSpecificOutput"}
    assert set(data["hookSpecificOutput"]) == {"hookEventName", "additionalContext"}
    text = _context(out)
    assert text is not None
    assert cid in text
    assert SUMMARY in text and ACK in text


def test_nudges_from_a_subfolder_cwd(repo: Path) -> None:
    cid = _new(repo, "decision", "Use a nudge")

    _, out = _nudge(_payload(repo / ".okf" / "decisions"))

    assert cid in (_context(out) or "")


def test_nudges_for_a_committed_concept_the_summary_is_behind(repo: Path) -> None:
    cid = _new(repo, "practice", "Nudge often")
    _commit(repo)

    _, out = _nudge(_payload(repo))

    assert cid in (_context(out) or "")


def test_nudges_with_path_when_the_payload_names_no_cwd(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cid = _new(repo, "decision", "Use a nudge")
    monkeypatch.chdir(tmp_path)

    _, out = _nudge(_payload(None), "--path", str(repo))

    assert cid in (_context(out) or "")


def test_nudges_as_text(repo: Path) -> None:
    cid = _new(repo, "decision", "Use a nudge")

    code, out = _nudge(_payload(repo), fmt="text")

    assert code == 0
    assert cid in out and SUMMARY in out and ACK in out
    assert not out.lstrip().startswith("{")


# r2: it is quiet -------------------------------------------------------------------


def test_quiet_when_the_summary_is_current(repo: Path) -> None:
    assert _nudge(_payload(repo)) == (0, "{}\n")
    assert _nudge(_payload(repo), fmt="text") == (0, "")


def test_quiet_after_the_summary_is_edited(repo: Path) -> None:
    _new(repo, "decision", "Use a nudge")
    summary = repo / SUMMARY
    summary.write_text(summary.read_text() + "\nMore.\n")

    assert _nudge(_payload(repo)) == (0, "{}\n")


def test_quiet_after_an_ack(repo: Path) -> None:
    _new(repo, "decision", "Use a nudge")
    assert _invoke("summary", "ack", "--path", str(repo)).exit_code == 0

    assert _nudge(_payload(repo)) == (0, "{}\n")


@pytest.mark.parametrize(
    "rel",
    [
        ".okf/log.md",
        ".okf/index.md",
        ".okf/decisions/index.md",
        ".okf/handoffs/2026-10-18-a.md",
        SUMMARY,
    ],
)
def test_quiet_when_only_a_file_the_summary_does_not_follow_changed(
    repo: Path, rel: str
) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((path.read_text() if path.exists() else "x\n") + "\nMore.\n")

    assert _nudge(_payload(repo)) == (0, "{}\n")


def test_quiet_for_the_same_set_and_a_grown_set_nudges_again(repo: Path) -> None:
    first = _new(repo, "decision", "Use a nudge")
    assert first in (_context(_nudge(_payload(repo))[1]) or "")

    assert _nudge(_payload(repo)) == (0, "{}\n")
    assert _nudge(_payload(repo, "ls")) == (0, "{}\n")

    second = _new(repo, "practice", "Nudge often")
    text = _context(_nudge(_payload(repo))[1]) or ""
    assert first in text and second in text
    assert _nudge(_payload(repo)) == (0, "{}\n")


def test_quiet_set_is_remembered_under_the_git_directory(repo: Path) -> None:
    _new(repo, "decision", "Use a nudge")
    _nudge(_payload(repo))

    state = repo / ".git" / "kmctl" / "summary-nudge"
    assert state.is_file()
    assert len(state.read_text().strip()) == len(hashlib.sha256().hexdigest())


def test_quiet_set_nudges_again_after_an_ack_and_a_new_change(repo: Path) -> None:
    cid = _new(repo, "decision", "Use a nudge")
    _nudge(_payload(repo))
    assert _invoke("summary", "ack", "--path", str(repo)).exit_code == 0
    _commit(repo)
    record = repo / ".okf" / "decisions" / f"{cid.split('/')[1]}.md"
    record.write_text(record.read_text() + "\nMore.\n")

    assert cid in (_context(_nudge(_payload(repo))[1]) or "")


def test_quiet_outside_a_git_repository(tmp_path: Path) -> None:
    (tmp_path / "r").mkdir()
    root = _init(tmp_path / "r", git=False)
    _new(root, "decision", "Use a nudge")

    assert _nudge(_payload(root)) == (0, "{}\n")


def test_quiet_without_a_bundle(tmp_path: Path) -> None:
    root = tmp_path / "r"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")

    assert _nudge(_payload(root)) == (0, "{}\n")
    assert _nudge(_payload(root), fmt="text") == (0, "")


BAD_STDIN = ["", "not json", "[]", '{"cwd": 3}', '{"cwd": "/no/such/folder"}']


@pytest.mark.parametrize("stdin", BAD_STDIN)
def test_quiet_on_unreadable_or_empty_stdin(
    repo: Path, stdin: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without an explicit --path, as the hook runs it, bad stdin says nothing even in a repository that is behind."""
    _new(repo, "decision", "Use a nudge")
    monkeypatch.chdir(repo)

    assert _nudge(stdin) == (0, "{}\n")
    assert _nudge(stdin, fmt="text") == (0, "")


@pytest.mark.parametrize("stdin", BAD_STDIN)
def test_nudges_with_an_explicit_path_and_unusable_stdin(
    repo: Path, tmp_path: Path, stdin: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A script or an agent's Bash gives --path; stdin with no usable cwd then falls back to it."""
    cid = _new(repo, "decision", "Use a nudge")
    monkeypatch.chdir(tmp_path)

    code, out = _nudge(stdin, "--path", str(repo), fmt="text")

    assert code == 0
    assert cid in out


def _json(stdin: str, *args: str) -> dict:
    code, out = _nudge(stdin, "--json", *args, fmt="text")
    assert code == 0, out
    return json.loads(out)


def test_nudges_as_json_and_a_repeat_has_no_nudge(repo: Path) -> None:
    cid = _new(repo, "decision", "Use a nudge")

    first = _json(_payload(repo))
    second = _json(_payload(repo))

    assert set(first) == {"behind", "concepts", "nudge"}
    assert first["behind"] is True and first["concepts"] == [cid]
    assert cid in first["nudge"] and ACK in first["nudge"]
    assert second == {"behind": True, "concepts": [cid], "nudge": None}


def test_quiet_as_json_when_current_or_failing(repo: Path, tmp_path: Path) -> None:
    quiet = {"behind": False, "concepts": [], "nudge": None}

    assert _json(_payload(repo)) == quiet
    assert _json("not json", "--path", str(tmp_path)) == quiet


def test_quiet_json_with_format_claude_is_refused(repo: Path) -> None:
    from typer.testing import CliRunner

    from kmctl import app

    result = CliRunner().invoke(
        app,
        ["summary", "nudge", "--format", "claude", "--json"],
        input=_payload(repo),
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "--json" in result.stderr and "--format" in result.stderr


def _tree(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_quiet_and_nudging_never_write_under_okf(repo: Path) -> None:
    _new(repo, "decision", "Use a nudge")
    before = _tree(repo / ".okf")

    _nudge(_payload(repo))
    _nudge(_payload(repo))

    assert _tree(repo / ".okf") == before


def _hook(
    command: str, cwd: Path, path: str, stdin: str, **env: str
) -> subprocess.CompletedProcess[str]:
    """Run a hook command as Claude Code does: sh -c, the payload on stdin."""
    return subprocess.run(
        ["/bin/sh", "-c", command],
        cwd=cwd,
        input=stdin,
        env={"PATH": path, "HOME": str(cwd), **env},
        capture_output=True,
        text=True,
        check=False,
    )


def test_quiet_hook_command_sets_kmctl_pinned() -> None:
    assert "KMCTL_PINNED=1 kmctl summary nudge --format claude" in (
        plugin.NUDGE_COMMAND
    )


def test_quiet_hook_command_in_a_pinned_project_never_calls_uvx(
    repo: Path, tmp_path: Path
) -> None:
    """A lock pinning another release would send the copy on PATH to uvx; the hook's KMCTL_PINNED=1 stops it."""
    lock = {
        "lockfile_version": "1",
        "dependencies": [
            {
                "repo_url": "jasperhg90/kmctl",
                "name": "kmctl",
                "virtual_path": "apm",
                "resolved_ref": "v0.5.1",
                "resolved_commit": "0123456789abcdef0123456789abcdef01234567",
            }
        ],
    }
    (repo / "apm.lock.yaml").write_text(yaml.safe_dump(lock))
    cid = _new(repo, "decision", "Use a nudge")
    fake = tmp_path / "fakebin"
    fake.mkdir()
    called = tmp_path / "uvx-called"
    (fake / "uvx").write_text(f"#!/bin/sh\ntouch {called}\necho '{{}}'\n")
    (fake / "uvx").chmod(0o755)
    path = (
        f"{_kmctl_bin(tmp_path)}:{fake}:{os.path.dirname(sys.executable)}:/usr/bin:/bin"
    )

    proc = _hook(plugin.NUDGE_COMMAND, repo, path, _payload(repo))

    assert proc.returncode == 0, proc.stderr
    assert not called.exists()
    assert cid in (_context(proc.stdout) or "")


def test_quiet_hook_command_prints_empty_object_when_the_verb_is_missing(
    repo: Path, tmp_path: Path
) -> None:
    """An older kmctl on PATH (v0.7.0, v0.8.0) exits 2 with a usage error; the hook prints {}."""
    old = tmp_path / "old"
    old.mkdir()
    (old / "kmctl").write_text(
        "#!/bin/sh\necho 'Usage: kmctl summary [OPTIONS] COMMAND [ARGS]...' >&2\n"
        "echo \"Error: No such command 'nudge'.\" >&2\nexit 2\n"
    )
    (old / "kmctl").chmod(0o755)

    proc = _hook(plugin.NUDGE_COMMAND, repo, f"{old}:/usr/bin:/bin", _payload(repo))

    assert proc.returncode == 0
    assert proc.stdout == "{}\n"


# r3: git only ----------------------------------------------------------------------


def test_git_only_the_nudge_never_calls_review_due(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = sys.modules["kmctl.review_due"].review_due

    def boom(*args: object, **kwargs: object) -> object:
        raise AssertionError("the nudge called review_due")

    patched = [
        mod
        for mod in list(sys.modules.values())
        if (getattr(mod, "__name__", "") or "").startswith("kmctl")
        and getattr(mod, "review_due", None) is real
    ]
    for mod in patched:
        monkeypatch.setattr(mod, "review_due", boom)
    assert sys.modules["kmctl.review_due"] in patched
    cid = _new(repo, "decision", "Use a nudge")

    code, out = _nudge(_payload(repo))

    assert code == 0
    assert cid in (_context(out) or "")


# r4: the hook entry and doctor ---------------------------------------------------


def _nudge_groups() -> list[dict]:
    return json.loads(HOOKS.read_text())["hooks"]["PostToolUse"]


def test_nudge_hook_ships_in_the_claude_package() -> None:
    [group] = _nudge_groups()

    assert group["matcher"] == "Write|Edit|MultiEdit|Bash"
    assert group["hooks"] == [plugin.nudge_hook_entry()]
    [entry] = group["hooks"]
    assert entry["type"] == "command"
    assert entry["timeout"] == 10
    assert entry["command"].startswith("command -v kmctl >/dev/null 2>&1 ||")
    assert entry["command"].endswith("exit 0")
    assert json.loads(HOOKS.read_text()) == antigravity.package_hooks("claude")


def test_nudge_hook_prints_empty_object_without_kmctl(repo: Path) -> None:
    proc = _hook(plugin.NUDGE_COMMAND, repo, "/usr/bin:/bin", _payload(repo))

    assert proc.returncode == 0
    assert proc.stdout == "{}\n"


def test_nudge_hook_is_not_in_the_antigravity_package() -> None:
    hooks = antigravity.package_hooks("antigravity")["hooks"]

    assert isinstance(hooks, dict) and "PostToolUse" not in hooks


# r5: the record --------------------------------------------------------------------


def _decision(title_part: str) -> Path:
    [path] = [
        p
        for p in (ROOT / ".okf" / "decisions").glob("[0-9]*.md")
        if title_part in str(field(front_matter(p), "title"))
    ]
    return path


def test_record_a_new_decision_supersedes_adr_0004() -> None:
    old = next((ROOT / ".okf" / "decisions").glob("0004-*.md"))
    new = _decision("summary nudge")
    new_text = new.read_text()

    assert field(front_matter(old), "status") == "deprecated"
    assert new.stem in old.read_text()
    assert old.stem in new_text
    for words in (
        "Not at the end of a turn. Just when anything in .okf changes",
        "But not .log",
        "3. Fine. Supersede.",
        "KMCTL_PINNED=1",
        "ADR 0026",
    ):
        assert words in new_text, words


def test_record_invariant_i1_names_both_hooks() -> None:
    text = (ROOT / ".okf" / "manifesto.md").read_text()
    i1 = text[text.index("**I1.") : text.index("**I2.")]

    assert "SessionStart" in i1 and "PostToolUse" in i1
    assert "kmctl summary nudge" in i1


@pytest.mark.parametrize("page", PAGES)
def test_record_page_describes_the_nudge_hook(page: str) -> None:
    text = (ROOT / page).read_text()

    assert "kmctl summary nudge" in text
    assert "PostToolUse" in text
