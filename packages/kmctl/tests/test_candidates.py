"""kmctl decision candidates: the changes since the newest decision record, for a judge (ADR 0047).

Each test builds a real git repository under tmp_path: ticket merges, pull
requests with and without ticket merges, a sync, plain commits and the
commits the verb leaves out.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kmctl import app

GIT = ["git", "-c", "user.email=t@example.com", "-c", "user.name=t"]
runner = CliRunner()


def _git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` with a fixed identity and return its stdout."""
    return subprocess.run(
        [*GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def _change(repo: Path, subject: str, *paths: str, body: str = "") -> None:
    """Commit ``subject`` (and ``body``), appending a line to each of ``paths``."""
    for rel in paths:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(f"{subject}\n")
        _git(repo, "add", rel)
    message = f"{subject}\n\n{body}" if body else subject
    _git(repo, "commit", "-q", "--allow-empty", "-m", message)


def _ticket(
    repo: Path, slug: str, summary: str, *paths: str, base: str = "main"
) -> None:
    """Merge a one-commit loop/SLUG branch into ``base`` as the loop harness does."""
    _git(repo, "switch", "-q", "-c", f"loop/{slug}", base)
    _change(repo, f"Inside {slug}", *paths)
    _git(repo, "switch", "-q", base)
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        f"Merge loop/{slug}: {summary}",
        f"loop/{slug}",
    )


def _pull(repo: Path, number: int, branch: str, base: str = "main") -> None:
    """Merge ``branch`` into ``base`` as GitHub merges pull request ``number``."""
    _git(repo, "switch", "-q", base)
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        f"Merge pull request #{number} from JasperHG90/{branch}\n\nTitle of #{number}",
        branch,
    )


def _subjects(repo: Path, *args: str) -> list[str]:
    """The subjects kmctl decision candidates lists, in its order."""
    result = runner.invoke(
        app, ["decision", "candidates", "--path", str(repo), "--json", *args]
    )
    assert result.exit_code == 0, result.output
    return [c["subject"] for c in json.loads(result.output)]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repository with ADR 0001, then every kind of change and the noise the verb skips."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _change(repo, "Start", "README.md")
    _change(repo, "Record ADR 0001", ".okf/decisions/0001-use-a-queue.md")
    _ticket(repo, "alpha", "Alpha lands.", "src/app/alpha.py")
    _change(repo, "Plain fix", "src/app/fix.py")
    for subject in (
        "loop: land alpha",
        "release: v0.2.0",
        "operator: manual commit",
        "chore; manual commits",
    ):
        _change(repo, subject, ".loop/state.json")
    # A pull request whose branch holds two ticket merges and a plain commit.
    _git(repo, "switch", "-q", "-c", "integration", "main")
    _ticket(repo, "beta", "Beta lands.", "src/app/beta.py", base="integration")
    _ticket(repo, "gamma", "Gamma lands.", "docs/gamma.md", base="integration")
    _change(repo, "Hand fix on integration", "scripts/x.py")
    _pull(repo, 53, "integration")
    # A pull request with no ticket merges stays one change.
    _git(repo, "switch", "-q", "-c", "small", "main")
    _change(repo, "Small change", "src/app/small.py")
    _pull(repo, 54, "small")
    # A release pull request is skipped.
    _git(repo, "switch", "-q", "-c", "release/v0.3.0", "main")
    _change(repo, "release: v0.3.0", "VERSION")
    _pull(repo, 55, "release/v0.3.0")
    # A sync brings in a commit made elsewhere.
    _git(repo, "switch", "-q", "-c", "github", "main")
    _change(repo, "Made on GitHub", "src/app/remote.py")
    _git(repo, "switch", "-q", "main")
    _change(repo, "Local move", "src/app/local.py")
    _git(
        repo,
        "merge",
        "-q",
        "--no-ff",
        "-m",
        "Merge remote-tracking branch 'origin/main'",
        "github",
    )
    return repo


EXPECTED = {
    "Merge loop/alpha: Alpha lands.",
    "Plain fix",
    "Merge loop/beta: Beta lands.",
    "Merge loop/gamma: Gamma lands.",
    "Hand fix on integration",
    "Merge pull request #54 from JasperHG90/small",
    "Local move",
    "Made on GitHub",
}


def test_split_lists_each_change_once_and_skips_the_noise(repo: Path) -> None:
    """One change per ticket, plain commit, ticket inside a pull request and small pull request; syncs read through; noise left out."""
    subjects = _subjects(repo)

    assert sorted(subjects) == sorted(EXPECTED)


def test_split_default_starts_after_the_newest_decision(repo: Path) -> None:
    """The default start is the commit that added the newest decision record, so earlier commits are not listed."""
    subjects = _subjects(repo)

    assert "Start" not in subjects
    assert "Record ADR 0001" not in subjects


def test_split_since_starts_after_the_given_commit(repo: Path) -> None:
    """--since lists only the changes after that commit."""
    small = _git(
        repo, "log", "--format=%H", "-1", "--grep", "Merge pull request #54"
    ).strip()

    assert sorted(_subjects(repo, "--since", small)) == ["Local move", "Made on GitHub"]


def test_split_without_decisions_reads_the_whole_history(tmp_path: Path) -> None:
    """A repository with no decision record lists from its first commit."""
    repo = tmp_path / "plain"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _change(repo, "First", "a.py")
    _change(repo, "Second", "b.py")

    assert sorted(_subjects(repo)) == ["First", "Second"]


def _by_subject(repo: Path) -> dict[str, dict]:
    """The verb's JSON objects keyed by subject."""
    result = runner.invoke(
        app, ["decision", "candidates", "--path", str(repo), "--json"]
    )
    assert result.exit_code == 0, result.output
    return {c["subject"]: c for c in json.loads(result.output)}


def test_fields_carry_what_a_judge_needs(repo: Path) -> None:
    """Each change has its sha, first parent, kind, subject, message, slug, plan, files, recorded, signals and score."""
    plan = repo / ".loop" / "plans" / "alpha" / "README.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("## Intent\n\nUse a queue instead of polling.\n")
    found = _by_subject(repo)
    alpha = found["Merge loop/alpha: Alpha lands."]
    pull = found["Merge pull request #54 from JasperHG90/small"]

    assert set(alpha) == {
        "sha", "parent", "kind", "subject", "message", "slug", "plan",
        "files", "recorded", "signals", "score",
    }  # fmt: skip
    assert alpha["kind"] == "ticket" and alpha["slug"] == "alpha"
    assert alpha["plan"] == ".loop/plans/alpha/README.md"
    assert alpha["signals"]["words"] is True
    assert ["A", "src/app/alpha.py"] in alpha["files"]
    assert alpha["parent"] == _git(repo, "rev-parse", f"{alpha['sha']}^1").strip()
    assert pull["kind"] == "pull" and pull["message"] == "Title of #54"
    assert found["Plain fix"]["kind"] == "commit" and found["Plain fix"]["plan"] is None
    assert all(c["score"] == sum(c["signals"].values()) for c in found.values())


def test_fields_recorded_names_added_and_amended_decisions(repo: Path) -> None:
    """A change that adds or amends a decision record names its number in recorded."""
    _change(repo, "Amend ADR 0001", ".okf/decisions/0001-use-a-queue.md")
    _change(repo, "Add ADR 0002", ".okf/decisions/0002-use-a-cache.md")
    _change(repo, "After ADR 0002", "src/app/after.py")
    found = _by_subject(repo)

    assert list(found) == ["After ADR 0002"]
    found = {
        c["subject"]: c
        for c in json.loads(
            runner.invoke(
                app,
                [
                    "decision",
                    "candidates",
                    "--path",
                    str(repo),
                    "--json",
                    "--since",
                    "HEAD~3",
                ],
            ).output
        )
    }
    assert found["Amend ADR 0001"]["recorded"] == ["0001"]
    assert found["Add ADR 0002"]["recorded"] == ["0002"]
    assert found["After ADR 0002"]["recorded"] == []


def test_fields_are_ordered_highest_score_first(repo: Path) -> None:
    """The list comes highest score first."""
    scores = [c["score"] for c in json.loads(
        runner.invoke(app, ["decision", "candidates", "--path", str(repo), "--json"]).output
    )]  # fmt: skip

    assert scores == sorted(scores, reverse=True)


def test_fields_table_and_nothing_written(repo: Path) -> None:
    """The default output is one line per change and a count; the repository's files and refs do not change."""
    status = _git(repo, "status", "--porcelain")
    refs = _git(repo, "show-ref")

    result = runner.invoke(app, ["decision", "candidates", "--path", str(repo)])

    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert len(lines) == len(EXPECTED) + 1
    assert lines[-1].startswith(f"{len(EXPECTED)} changes")
    assert _git(repo, "status", "--porcelain") == status
    assert _git(repo, "show-ref") == refs


def test_refuses_outside_a_git_repository(tmp_path: Path) -> None:
    """Outside a git repository it exits 1 with one stderr line naming the fix."""
    result = runner.invoke(app, ["decision", "candidates", "--path", str(tmp_path)])

    assert result.exit_code == 1
    assert "kmctl decision candidates: refused:" in result.stderr
    assert "not a git repository" in result.stderr
    assert "--path" in result.stderr


def test_refuses_a_since_that_names_no_commit(repo: Path) -> None:
    """A --since naming no commit exits 1 and says what to give instead."""
    result = runner.invoke(
        app, ["decision", "candidates", "--path", str(repo), "--since", "no-such-ref"]
    )

    assert result.exit_code == 1
    assert "--since 'no-such-ref' names no commit" in result.stderr
    assert "e.g. --since" in result.stderr


ROOT = Path(__file__).resolve().parents[3]


def test_reference_documents_the_verb() -> None:
    """docs/reference/commands.md lists the verb in its summary table and gives it a section with every option."""
    text = (ROOT / "docs" / "reference" / "commands.md").read_text()
    section = text.split("### `kmctl decision candidates`", 1)[1].split("\n### ", 1)[0]

    assert "| `kmctl decision candidates` |" in text
    for option in ("`--since REF`", "`--path DIR`", "`--json`"):
        assert option in section
    assert "writes nothing" in section


def test_decision_0047_records_the_split() -> None:
    """Decision 0047 matches the decision schema, names the verb and the skill, says the user decides, and links ADR 0046 and the prototype."""
    from jsonschema import Draft202012Validator

    from kmctl.kinds import schema, skeleton
    from kmctl.okf import front_matter

    record = next((ROOT / ".okf" / "decisions").glob("0047-*.md"))
    meta = json.loads(json.dumps(front_matter(record), default=str))
    text = record.read_text()
    headings = [line[3:] for line in text.splitlines() if line.startswith("## ")]

    assert list(Draft202012Validator(schema("decision")).iter_errors(meta)) == []
    assert headings[:3] == skeleton("decision")
    assert "`kmctl decision candidates` lists" in text
    assert "decision-gaps skill judges every change and reports" in text
    assert "The user decides" in text
    assert "(0046-kmctl-works-from-code-toward-knowledge" in text
    assert "(../prototypes/decision-gaps/README.md)" in text


def test_split_default_ignores_a_decision_not_yet_committed(repo: Path) -> None:
    """A record written but not committed does not move the default start to the whole history."""
    draft = repo / ".okf" / "decisions" / "0002-use-a-cache.md"
    draft.write_text("draft\n")
    _git(repo, "add", str(draft))

    assert sorted(_subjects(repo)) == sorted(EXPECTED)


def test_split_from_a_subdirectory_reads_the_whole_repository(repo: Path) -> None:
    """--path inside the repository lists the same changes and finds plans at the top level."""
    plan = repo / ".loop" / "plans" / "alpha" / "README.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("## Intent\n\nUse a queue.\n")
    result = runner.invoke(
        app,
        ["decision", "candidates", "--path", str(repo / "src" / "app"), "--json"],
    )

    found = {c["subject"]: c for c in json.loads(result.output)}
    assert sorted(found) == sorted(EXPECTED)
    assert (
        found["Merge loop/alpha: Alpha lands."]["plan"] == ".loop/plans/alpha/README.md"
    )


def test_fields_words_signal_reads_across_line_breaks(tmp_path: Path) -> None:
    """A phrase such as "instead of" split by a wrapped commit body still counts."""
    repo = tmp_path / "wrapped"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _change(
        repo,
        "Use a queue",
        "q.py",
        body="We poll a queue instead\nof the old cron job.",
    )
    found = json.loads(
        runner.invoke(
            app, ["decision", "candidates", "--path", str(repo), "--json"]
        ).output
    )

    assert found[0]["signals"]["words"] is True


def test_refuses_a_repository_with_no_commits(tmp_path: Path) -> None:
    """A repository with no commits exits 1 with one line saying to commit first."""
    _git(tmp_path, "init", "-q", "-b", "main")
    result = runner.invoke(app, ["decision", "candidates", "--path", str(tmp_path)])

    assert result.exit_code == 1
    assert "has no commits yet; commit something" in result.stderr
