"""The bundle summary, .okf/summary.md: its kind, word limit, freshness rule and ack (ADR 0027)."""

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from conftest import okf_validate
from test_action import _kmctl_bin
from test_action import _run as _run_action
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.kinds import SUMMARY_SECTIONS
from kmctl.okf import field, front_matter
from kmctl.scaffold import BLOCK, SUMMARY_LINE, SUMMARY_PROMPTS
from kmctl.summary import ack

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ".okf/summary.md"
#: How ack writes checked.at: a UTC timestamp to the second.
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
#: The summary's sections, by what a reader needs rather than by concept folder.
FOUR_SECTIONS = [
    "The project",
    "How it works",
    "What it has settled",
    "Where it stands",
]
#: A prompt that asks for a link or an entry per concept, as the old ones did.
LINK_EACH = re.compile(r"\b(link|list)\w*\s+each\b", re.IGNORECASE)
#: Where the guidance on writing the summary lives, besides the AGENTS.md block.
GUIDANCE = (
    ".claude/rules/okf-bundle.md",
    "apm/claude/.apm/instructions/okf-bundle.instructions.md",
    "apm/antigravity/.apm/instructions/okf-bundle.instructions.md",
    "docs/reference/commands.md",
)


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _git(root: Path, *args: str) -> None:
    """Run git in ``root`` with a fixed author, failing the test on error."""
    env = os.environ | {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)


def _commit(root: Path, message: str = "c") -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


def _init(root: Path, git: bool = True) -> Path:
    """A repository set up by kmctl init; with ``git``, a git repository with it committed."""
    if git:
        _git(root, "init", "-q", "-b", "main")
    result = _invoke("init", "--path", str(root))
    assert result.exit_code == 0, result.output
    if git:
        _commit(root, "init")
    return root


def _new(root: Path, kind: str, title: str) -> str:
    """Add a concept with kmctl new; returns its id."""
    result = _invoke(
        "new", kind, title, "--description", "One.", "--path", str(root), "--json"
    )
    assert result.exit_code == 0, result.output
    return json.loads(result.stdout)["id"]


def _due(root: Path) -> dict[str, list[str]]:
    result = _invoke("review", "due", "--path", str(root), "--json")
    assert result.exit_code == 0, result.output
    return {d["id"]: d["reasons"] for d in json.loads(result.stdout)["due"]}


def _summary_reasons(root: Path) -> list[str] | None:
    return _due(root).get("summary")


def _append(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)


def _body(words: int) -> str:
    return "# Summary\n\n" + " ".join(["word"] * (words - 2)) + "\n"


def _set_body(root: Path, body: str) -> None:
    path = root / SUMMARY
    text = path.read_text(encoding="utf-8")
    end = text.index("\n---", 4) + len("\n---\n")
    path.write_text(text[:end] + "\n" + body, encoding="utf-8")


def _ack(root: Path, *args: str) -> Result:
    return _invoke("summary", "ack", "--path", str(root), *args)


# r1: the kind and init ---------------------------------------------------------


def test_init_writes_the_summary_sections(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    path = tmp_path / SUMMARY
    text = path.read_text(encoding="utf-8")
    headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    index = (tmp_path / ".okf/index.md").read_text(encoding="utf-8")

    assert field(front_matter(path), "type") == "summary"
    assert headings == SUMMARY_SECTIONS == FOUR_SECTIONS
    for heading in SUMMARY_SECTIONS:
        after = text.split(f"## {heading}\n\n", 1)[1].split("\n", 1)[0]
        assert after and not after.startswith("#"), heading
        assert after == SUMMARY_PROMPTS[heading]
        assert not LINK_EACH.search(after), after
    assert "evidence" in SUMMARY_PROMPTS["What it has settled"]
    assert "never one bullet per decision" in SUMMARY_PROMPTS["What it has settled"]
    assert "theme by theme" not in text
    assert "](summary.md)" in index
    check = okf_validate(tmp_path / ".okf")
    assert check.returncode == 0, check.stdout + check.stderr
    assert _invoke("check", "--path", str(tmp_path)).exit_code == 0


def test_init_summary_kind_has_a_schema_with_its_sections(tmp_path: Path) -> None:
    result = _invoke("schema", "summary")

    assert result.exit_code == 0, result.output
    schema = json.loads(result.stdout)
    assert schema["properties"]["type"]["const"] == "summary"
    assert set(schema["properties"]) == {
        "type",
        "title",
        "description",
        "tags",
        "generated",
        "checked",
    }
    assert schema["x-kmctl-sections"] == SUMMARY_SECTIONS == FOUR_SECTIONS
    assert set(schema["properties"]["checked"]["properties"]) == {"at", "against"}


def test_init_summary_is_not_a_kmctl_new_kind(tmp_path: Path) -> None:
    _init(tmp_path, git=False)

    result = _invoke(
        "new", "summary", "Another", "--description", "One.", "--path", str(tmp_path)
    )
    help_text = _invoke("new", "--help").stdout

    assert result.exit_code != 0
    assert "summary" not in help_text.lower()
    assert not list((tmp_path / ".okf").glob("**/another*"))


# r2: the word limit ------------------------------------------------------------


@pytest.mark.parametrize(("words", "fails"), [(500, False), (501, True)])
def test_word_limit(tmp_path: Path, words: int, fails: bool) -> None:
    _init(tmp_path, git=False)
    _set_body(tmp_path, _body(words))

    result = _invoke("check", "--path", str(tmp_path), "--json")
    findings = [f for f in json.loads(result.stdout) if f["check"] == "summary"]

    assert (result.exit_code == 1) is fails, result.stdout
    if fails:
        [finding] = findings
        assert finding["level"] == "error"
        assert finding["file"] == SUMMARY
        assert "501 words" in finding["message"]
        assert "500" in finding["message"].replace("501", "")
    else:
        assert findings == []


def test_word_limit_ignores_front_matter(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    _set_body(tmp_path, _body(500))
    path = tmp_path / SUMMARY
    text = path.read_text(encoding="utf-8")
    long = " ".join(["tag"] * 50)
    path.write_text(text.replace("tags: [summary]", f"tags: [summary]\n# {long}"))

    assert _invoke("check", "--path", str(tmp_path)).exit_code == 0


def test_word_limit_links_are_checked(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    _set_body(tmp_path, "# Summary\n\nSee [the code](../src/missing.py).\n")

    result = _invoke("check", "--path", str(tmp_path), "--json")

    assert result.exit_code == 1
    assert any(
        f["check"] == "link" and f["file"] == SUMMARY for f in json.loads(result.stdout)
    )


# r3: freshness -----------------------------------------------------------------


def test_freshness_a_decision_committed_after_the_summary(tmp_path: Path) -> None:
    root = _init(tmp_path)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)

    assert _summary_reasons(root) == [f"concepts changed: {cid}"]


def test_freshness_names_every_changed_concept(tmp_path: Path) -> None:
    root = _init(tmp_path)
    ids = [
        _new(root, "decision", "Use a queue"),
        _new(root, "practice", "Measure first"),
        _new(root, "proposal", "Split the parser"),
        _new(root, "prototype", "Parser speed"),
    ]
    _append(root, ".okf/architecture/overview.md", "# Overview\n\n## Depicts\n")
    _append(root, ".okf/manifesto.md", "More.\n")
    _commit(root)

    expected = sorted([*ids, "architecture/overview", "manifesto"])
    assert _summary_reasons(root) == ["concepts changed: " + ", ".join(expected)]


def test_freshness_same_commit_as_the_summary_is_covered(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _new(root, "decision", "Use a queue")
    _append(root, SUMMARY, "The queue.\n")
    _commit(root)

    assert _summary_reasons(root) is None


def test_freshness_summary_in_a_later_commit_is_covered(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _new(root, "decision", "Use a queue")
    _commit(root)
    _append(root, SUMMARY, "The queue.\n")
    _commit(root)

    assert _summary_reasons(root) is None


def test_freshness_working_tree_changes_count(tmp_path: Path) -> None:
    root = _init(tmp_path)
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    _append(root, first.relative_to(root).as_posix(), "An edit.\n")
    new = _new(root, "decision", "Untracked one")

    assert _summary_reasons(root) == [
        f"concepts changed: decisions/{first.stem}, {new}"
    ]


def test_freshness_never_for_log_index_or_handoff(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _new(root, "handoff", "Where it stopped")
    _append(root, ".okf/log.md", "- A line.\n")
    _append(root, ".okf/index.md", "- [X](x/index.md): x.\n")
    _append(root, ".okf/decisions/index.md", "- more\n")
    _append(root, ".okf/prototypes/speed/run.py", "print(1)\n")
    _append(root, ".okf/prototypes/speed/README.md.bak", "x\n")
    _commit(root)
    _append(root, ".okf/log.md", "- An uncommitted line.\n")

    assert _summary_reasons(root) is None


def test_freshness_skipped_without_git_history(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    _new(tmp_path, "decision", "Use a queue")

    assert _summary_reasons(tmp_path) is None


def test_freshness_skipped_in_a_shallow_clone(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    origin.mkdir()
    _init(origin)
    _new(origin, "decision", "Use a queue")
    _commit(origin)
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", origin.resolve().as_uri(), str(clone)],
        check=True,
        capture_output=True,
    )

    assert _summary_reasons(origin) is not None
    assert _summary_reasons(clone) is None


# r4: what clears it, and that it never fails ------------------------------------


def test_clears_on_an_uncommitted_edit(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _new(root, "decision", "Use a queue")
    _commit(root)
    assert _summary_reasons(root)

    _append(root, SUMMARY, "The queue.\n")

    assert _summary_reasons(root) is None


def test_clears_on_ack_and_writes_only_checked(tmp_path: Path) -> None:
    root = _init(tmp_path)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)
    path = root / SUMMARY
    before = {
        p: p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    old = path.read_text(encoding="utf-8")

    result = _ack(root, "--json")

    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    at = data["at"]
    assert data == {"path": SUMMARY, "at": at, "against": [cid]}
    assert STAMP.fullmatch(at), at
    assert at.startswith(datetime.now(UTC).date().isoformat())
    new = path.read_text(encoding="utf-8")
    assert new == old.replace(
        "\n---\n",
        f"\nchecked:\n  at: {at}\n  against:\n    - {cid}\n---\n",
        1,
    )
    after = {
        p: p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    assert {p for p in after if after[p] != before.get(p)} == {path}
    assert _summary_reasons(root) is None
    _commit(root, "ack")
    assert _summary_reasons(root) is None


def test_clears_ack_again_after_the_same_concept_changes_again(
    tmp_path: Path,
) -> None:
    """A second ack on the same day, against the same ids, still changes the summary."""
    root = _init(tmp_path)
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    rel = first.relative_to(root).as_posix()
    _append(root, rel, "An edit.\n")
    _commit(root)
    assert _ack(root).exit_code == 0
    _commit(root, "ack")
    _append(root, rel, "Another edit.\n")
    _commit(root)
    before = (root / SUMMARY).read_bytes()

    result = _ack(root)

    assert result.exit_code == 0, result.output
    assert (root / SUMMARY).read_bytes() != before
    assert _summary_reasons(root) is None
    check = _invoke("check", "--path", str(root), "--json")
    assert [f for f in json.loads(check.stdout) if f["check"] == "summary"] == []
    _commit(root, "ack again")
    assert _summary_reasons(root) is None


def test_clears_ack_in_the_same_second_still_changes_the_summary(
    tmp_path: Path,
) -> None:
    root = _init(tmp_path)
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    rel = first.relative_to(root).as_posix()
    when = datetime(2026, 10, 18, 20, 0, 0, tzinfo=UTC)
    _append(root, rel, "An edit.\n")
    _commit(root)
    assert ack(root, now=when).at == "2026-10-18T20:00:00Z"
    _commit(root, "ack")
    _append(root, rel, "Another edit.\n")
    _commit(root)

    again = ack(root, now=when)

    assert again.at == "2026-10-18T20:00:01Z"
    assert _summary_reasons(root) is None


def test_clears_ack_replaces_an_older_checked(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _new(root, "decision", "Use a queue")
    _commit(root)
    assert _ack(root).exit_code == 0
    _commit(root, "ack")
    second = _new(root, "practice", "Measure first")
    _commit(root)

    assert _ack(root).exit_code == 0

    meta = front_matter(root / SUMMARY)
    assert field(meta, "checked.against") == [second]
    assert (root / SUMMARY).read_text(encoding="utf-8").count("checked:") == 1


def test_clears_ack_writes_nothing_when_current(tmp_path: Path) -> None:
    root = _init(tmp_path)
    before = (root / SUMMARY).read_bytes()

    result = _ack(root)

    assert result.exit_code == 0, result.output
    assert "nothing to ack" in result.stdout
    assert (root / SUMMARY).read_bytes() == before


def test_clears_ack_refuses_without_git(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    before = (tmp_path / SUMMARY).read_bytes()

    result = _ack(tmp_path)

    assert result.exit_code == 1
    assert "git history" in result.stderr
    assert (tmp_path / SUMMARY).read_bytes() == before


def test_clears_never_unverified_or_stale_after(tmp_path: Path) -> None:
    root = _init(tmp_path)
    path = root / SUMMARY
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "tags: [summary]", "tags: [summary]\nstale_after: 2020-01-01T00:00:00Z"
        ),
        encoding="utf-8",
    )
    _commit(root)

    due = _due(root)

    assert "summary" not in due
    assert "manifesto" in due  # the same rules still list other concepts


def test_clears_check_reports_a_stale_summary_without_failing(tmp_path: Path) -> None:
    root = _init(tmp_path)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)

    result = _invoke("check", "--path", str(root), "--json")
    text = _invoke("check", "--path", str(root)).stdout

    assert result.exit_code == 0, result.stdout
    [finding] = [f for f in json.loads(result.stdout) if f["check"] == "summary"]
    assert finding["level"] == "warning"
    assert cid in finding["message"] and "kmctl summary ack" in finding["message"]
    assert "all checks passed, 1 warning" in text


def test_clears_ci_action_reports_a_stale_summary_without_failing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _init(root)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)

    proc, report = _run_action(root, _kmctl_bin(tmp_path), tmp_path)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    check, due = report.split("## kmctl review due", 1)
    assert "summary is behind" in check and cid in check
    assert re.search(rf"due\s+summary\s+\(concepts changed: {re.escape(cid)}\)", due)


# r5: checked is a named extension field ----------------------------------------


def test_checked_fields_read_through_okf_field(tmp_path: Path) -> None:
    root = _init(tmp_path)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)
    assert _ack(root).exit_code == 0

    meta = front_matter(root / SUMMARY)

    at = field(meta, "checked.at")
    assert isinstance(at, datetime) and at.tzinfo is not None
    assert at.date() == datetime.now(UTC).date()
    assert field(meta, "checked.against") == [cid]
    assert set(field(meta, "checked")) == {"at", "against"}


def test_check_warns_on_checked_against_a_concept_that_does_not_exist(
    tmp_path: Path,
) -> None:
    """The reproduction in kmctl#34: an id added by hand under checked.against."""
    root = _init(tmp_path)
    cid = _new(root, "decision", "Use a queue")
    _commit(root)
    assert _ack(root).exit_code == 0
    path = root / SUMMARY
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            f"    - {cid}\n", f"    - {cid}\n    - decisions/0099-does-not-exist\n"
        ),
        encoding="utf-8",
    )
    _commit(root, "ack")

    result = _invoke("check", "--path", str(root), "--json")
    text = _invoke("check", "--path", str(root)).stdout

    assert result.exit_code == 0, result.stdout
    assert [f for f in json.loads(result.stdout) if f["check"] == "summary"] == [
        {
            "check": "summary",
            "file": SUMMARY,
            "line": None,
            "message": (
                "checked.against names decisions/0099-does-not-exist, which is "
                "not a concept in the bundle; remove it from the list"
            ),
            "level": "warning",
        }
    ]
    assert "all checks passed, 1 warning" in text


def test_ack_leaves_out_a_concept_that_was_deleted(tmp_path: Path) -> None:
    root = _init(tmp_path)
    kept = _new(root, "decision", "Use a queue")
    _commit(root)
    assert _ack(root).exit_code == 0
    _commit(root, "ack")
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    first.unlink()
    _append(root, f".okf/{kept}.md", "An edit.\n")
    _commit(root, "delete 0001")

    result = _ack(root, "--json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["against"] == [kept]
    assert field(front_matter(root / SUMMARY), "checked.against") == [kept]
    check = _invoke("check", "--path", str(root), "--json")
    assert [f for f in json.loads(check.stdout) if f["check"] == "summary"] == []


def test_ack_after_a_rename_names_only_the_new_id(tmp_path: Path) -> None:
    root = _init(tmp_path)
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    _git(root, "mv", str(first), str(first.with_name("0001-renamed.md")))
    _commit(root, "rename 0001")

    result = _ack(root, "--json")

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["against"] == ["decisions/0001-renamed"]


def test_ack_after_only_a_deletion_writes_an_empty_list(tmp_path: Path) -> None:
    root = _init(tmp_path)
    (first,) = (root / ".okf/decisions").glob("0001-*.md")
    first.unlink()
    _commit(root, "delete 0001")

    result = _ack(root)

    assert result.exit_code == 0, result.output
    first_line = result.stdout.splitlines()[0]
    assert re.fullmatch(
        rf"checked {SUMMARY} at {STAMP.pattern} against none", first_line
    )
    assert front_matter(root / SUMMARY)["checked"]["against"] == []
    assert _summary_reasons(root) is None


def test_checked_named_in_invariant_i4() -> None:
    manifesto = (ROOT / ".okf" / "manifesto.md").read_text(encoding="utf-8")
    i4 = manifesto[manifesto.index("- **I4.") :].split("\n- **", 1)[0]

    assert "`handoff_key`" in i4 and "`checked`" in i4
    assert "The only one is" not in i4


# r6: the AGENTS.md block ---------------------------------------------------------


def test_summary_block_points_to_it_and_gives_the_duty(tmp_path: Path) -> None:
    _init(tmp_path, git=False)
    written = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")

    for text in (BLOCK, written):
        assert "Start at `.okf/summary.md`" in text
        assert "Start at `.okf/index.md`" not in text
        duty = next(line for line in text.splitlines() if "kmctl summary ack" in line)
        assert "add or change a concept" in duty
        assert "update `.okf/summary.md`" in duty


def test_guidance_says_the_summary_distils_the_knowledge() -> None:
    duty = next(line for line in BLOCK.splitlines() if "kmctl summary ack" in line)
    texts = {"the block's duty": duty, "SUMMARY_LINE": SUMMARY_LINE}
    texts |= {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in GUIDANCE}

    for name, text in texts.items():
        assert "theme by theme" not in text, name
        assert "each theme linking" not in text, name
    for name in ("the block's duty", *GUIDANCE):
        flat = " ".join(texts[name].split())
        assert "distils what the knowledge says as a whole" in flat, name
        assert "the indexes list the concepts" in flat, name
    reference = " ".join(texts["docs/reference/commands.md"].split())
    assert "(The project, How it works, What it has settled, Where it stands)" in (
        reference
    )
    assert "Decisions, Architecture, Open work" not in reference


# r7: this repository -------------------------------------------------------------


def _sections(body: str) -> dict[str, str]:
    """Each ``##`` section of ``body`` by its heading, with its text."""
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def _bullets(text: str) -> list[str]:
    """The top-level bullets in ``text``, each with its wrapped lines joined."""
    return [" ".join(b.split()) for b in re.split(r"^- ", text, flags=re.MULTILINE)[1:]]


def _single_decision_link(bullet: str) -> bool:
    """A bullet whose only link points at one decision record."""
    links = re.findall(r"\]\(([^)\s]+)\)", bullet)
    return len(links) == 1 and links[0].startswith("decisions/")


def test_this_repository_has_a_summary_within_the_limit() -> None:
    path = ROOT / SUMMARY
    text = path.read_text(encoding="utf-8")
    end = text.index("\n---", 4) + len("\n---")
    words = len(text[end:].split())
    headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]
    links = re.findall(r"\]\(([^)\s]+)\)", text[end:])

    assert field(front_matter(path), "type") == "summary"
    assert 0 < words <= 500, words
    assert headings == SUMMARY_SECTIONS == FOUR_SECTIONS
    assert links
    for link in links:
        assert (path.parent / link.split("#")[0]).resolve().is_file(), link
    assert any(link.startswith("decisions/0") for link in links)
    assert any(link.startswith("architecture/") for link in links)
    assert "](summary.md)" in (ROOT / ".okf/index.md").read_text(encoding="utf-8")


def test_this_repository_summary_does_not_list_the_decisions() -> None:
    path = ROOT / SUMMARY
    text = path.read_text(encoding="utf-8")
    body = text[text.index("\n---", 4) + len("\n---") :]

    for heading, section in _sections(body).items():
        bullets = _bullets(section)
        single = [b for b in bullets if _single_decision_link(b)]
        assert len(single) * 2 <= len(bullets), (heading, single)
    assert "theme by theme" not in text
    assert "theme by theme" not in (ROOT / ".okf/index.md").read_text(encoding="utf-8")


def test_this_repository_single_decision_link_is_what_the_check_counts() -> None:
    listed = _bullets(
        "- **A.** One ([ADR 0004](decisions/0004-x.md)).\n"
        "- **B.** Two ([ADR 0005](decisions/0005-x.md),\n"
        "  [ADR 0023](decisions/0023-x.md)).\n"
        "- **C.** The [overview](architecture/overview.md).\n"
    )

    assert [_single_decision_link(b) for b in listed] == [True, False, False]


def test_this_repository_passes_kmctl_check() -> None:
    result = _invoke("check", "--path", str(ROOT))

    assert result.exit_code == 0, result.stdout


def test_this_repository_records_the_decision_and_the_verb() -> None:
    decisions = [
        p.read_text(encoding="utf-8") for p in (ROOT / ".okf/decisions").glob("0*.md")
    ]
    reference = (ROOT / "docs/reference/commands.md").read_text(encoding="utf-8")

    [record] = [d for d in decisions if "kmctl summary ack" in d and "500" in d]
    assert "summary.md" in record and "commit" in record
    assert "### `kmctl summary ack`" in reference


# drop-summary-nudge r2: the summary verbs are ack only --------------------------


def test_summary_has_no_nudge_verb() -> None:
    help_text = _invoke("summary", "--help").output
    assert "ack" in help_text
    assert "nudge" not in help_text
    assert _invoke("summary", "nudge").exit_code != 0
