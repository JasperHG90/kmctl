"""The check on Hermes' rewrite of the release notes: keep it or keep the draft (ADR 0035)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "hermes_release_notes.py"

DRAFT = """\
## What changed

- Deferred hardening from hermes-workflows, reviewer finding f2 in review round 1. (`hermes-workflows-reviewer-f2`)
- kmaudit mcp starts a stdio MCP server whose tools are kmaudit's verbs. (`kmaudit-mcp`)
- Release from one run with per-package notes (#42)

## Other changes

- check: make the summary word limit a warning, add --strict

## Install

```sh
uv tool install git+https://github.com/JasperHG90/kmctl@v0.13.0#subdirectory=packages/kmctl
```

**Full diff**: https://github.com/JasperHG90/kmctl/compare/v0.12.1...v0.13.0
"""

WHAT_CHANGED = DRAFT.split("## Other changes")[0].rstrip()

REWRITE = """\
## What changed

- Deferred hardening from hermes-workflows, reviewer finding f2 in review round 1. (`hermes-workflows-reviewer-f2`)
- Drive the audit from any MCP harness with `kmaudit mcp`. (`kmaudit-mcp`)
- Release kmctl or kmaudit from one run, each with its own notes. (#42)

## Other changes

- check: make the summary word limit a warning, add --strict

## Install

```sh
uv tool install git+https://github.com/JasperHG90/kmctl@v0.13.0#subdirectory=packages/kmctl
```

**Full diff**: https://github.com/JasperHG90/kmctl/compare/v0.12.1...v0.13.0
"""


def _run(
    tmp_path: Path, response: str | None, *, before: bool = True
) -> tuple[subprocess.CompletedProcess[bytes], Path]:
    """Run the script on DRAFT and ``response`` (no file when None); return it and the --before path."""
    draft = tmp_path / "draft.md"
    draft.write_text(DRAFT)
    resp = tmp_path / "response.md"
    if response is not None:
        resp.write_text(response)
    out = tmp_path / "before.md"
    args = [sys.executable, str(SCRIPT), str(draft), str(resp)]
    if before:
        args += ["--before", str(out)]
    res = subprocess.run(args, capture_output=True, check=False)
    return res, out


def test_a_good_rewrite_is_kept_with_the_draft_s_what_changed_beside_it(
    tmp_path: Path,
) -> None:
    """A rewrite passing every check is printed, and --before gets the draft's What changed, collapsed."""
    res, before = _run(tmp_path, REWRITE)

    assert res.returncode == 0
    assert res.stdout.decode() == REWRITE
    assert b"::warning::" not in res.stderr
    text = before.read_text()
    assert "<summary>Draft before Hermes</summary>" in text
    assert WHAT_CHANGED in text
    assert "## Other changes" not in text
    assert text.lstrip().startswith("<details>")
    assert text.rstrip().endswith("</details>")


def test_cleaning_strips_comments_a_preamble_and_a_wrapping_fence(
    tmp_path: Path,
) -> None:
    """HTML comments (a line holding only one goes whole), text before the first heading and a fence round the reply go."""
    wrapped = (
        "Here are the rewritten notes:\n\n```markdown\n"
        + REWRITE.replace("## Install", "<!-- keep -->\n## Install")
        + "```\n<!-- hermes: done -->\n"
    )

    res, _ = _run(tmp_path, wrapped)

    assert res.returncode == 0
    assert res.stdout.decode() == REWRITE
    assert b"::warning::" not in res.stderr


def test_a_reply_wrapped_in_a_fence_alone_is_kept(tmp_path: Path) -> None:
    """A fence round the whole reply, with no preamble, is stripped."""
    res, _ = _run(tmp_path, "```markdown\n" + REWRITE + "```\n")

    assert res.stdout.decode() == REWRITE


@pytest.mark.parametrize(
    ("name", "response"),
    [
        ("missing", None),
        ("empty", "<!-- nothing to say -->\n\n"),
        ("headings", REWRITE.replace("## Install\n", "")),
        (
            "headings",
            REWRITE.replace("## Other changes", "## Other changes\n\n## Extra"),
        ),
        (
            "tail",
            REWRITE.replace("compare/v0.12.1...v0.13.0", "compare/v0.12.0...v0.13.0"),
        ),
        ("tail", REWRITE.replace("add --strict", "add a --strict flag")),
        (
            "ref-added",
            REWRITE.replace(
                "(#42)\n", "(#42)\n- Faster startup on large repositories. (#43)\n"
            ),
        ),
        ("ref-added", REWRITE.replace("(`kmaudit-mcp`)", "(`kmaudit-server`)")),
        (
            "ref-dropped",
            REWRITE.replace(
                "- Drive the audit from any MCP harness with `kmaudit mcp`. (`kmaudit-mcp`)\n",
                "",
            ),
        ),
        (
            "bullet-without-ref",
            REWRITE.replace("(#42)\n", "(#42)\n- Also a few small fixes.\n"),
        ),
    ],
)
def test_a_failed_check_prints_the_draft_byte_for_byte_and_names_the_check(
    tmp_path: Path, name: str, response: str | None
) -> None:
    """Each failure prints the draft unchanged, warns naming the check, writes no --before and exits 0."""
    (tmp_path / "before.md").write_text("stale")

    res, before = _run(tmp_path, response)

    assert res.returncode == 0
    assert res.stdout == DRAFT.encode()
    warnings = [
        ln for ln in res.stderr.decode().splitlines() if ln.startswith("::warning::")
    ]
    assert len(warnings) == 1
    assert f"the {name} check" in warnings[0]
    assert not before.exists()


def test_an_empty_response_path_falls_back_to_the_draft(tmp_path: Path) -> None:
    """A Hermes step that failed gives an empty response_file output; the draft stands."""
    draft = tmp_path / "draft.md"
    draft.write_text(DRAFT)

    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(draft), ""], capture_output=True, check=False
    )

    assert res.returncode == 0
    assert res.stdout == DRAFT.encode()
    assert "the missing check" in res.stderr.decode()


def test_trailing_whitespace_in_the_tail_is_ignored(tmp_path: Path) -> None:
    """The tail matches the draft line by line, ignoring trailing whitespace."""
    res, _ = _run(tmp_path, REWRITE.replace("add --strict\n", "add --strict   \n"))

    assert b"::warning::" not in res.stderr
    assert "add --strict   " in res.stdout.decode()


def test_without_before_a_kept_rewrite_is_still_printed(tmp_path: Path) -> None:
    """--before is optional."""
    res, before = _run(tmp_path, REWRITE, before=False)

    assert res.returncode == 0
    assert res.stdout.decode() == REWRITE
    assert not before.exists()


def test_a_response_that_is_not_utf8_falls_back_to_the_draft(tmp_path: Path) -> None:
    """A response file that does not decode counts as missing, so the run never fails on it."""
    draft = tmp_path / "draft.md"
    draft.write_text(DRAFT)
    resp = tmp_path / "response.md"
    resp.write_bytes(b"## What changed\n\n- \xff\xfe broken (#42)\n")

    res = subprocess.run(
        [sys.executable, str(SCRIPT), str(draft), str(resp)],
        capture_output=True,
        check=False,
    )

    assert res.returncode == 0
    assert res.stdout == DRAFT.encode()
    assert "the missing check" in res.stderr.decode()
