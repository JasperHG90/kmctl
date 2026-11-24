import json
import subprocess
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

DRAFT = ".okf/decisions/0002-use-a-queue.md"


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path, email: str | None = "ada@example.com") -> Path:
    """A git repository with init's decision 0001 and a draft decision 0002."""
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    if email:
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", email], check=True
        )
    assert _invoke("init", "--path", str(root)).exit_code == 0
    result = _invoke(
        "new",
        "decision",
        "Use a queue",
        "--description",
        "Use a queue.",
        "--draft",
        "--path",
        str(root),
    )
    assert result.exit_code == 0, result.output
    return root


def _accept(root: Path, *extra: str) -> Result:
    return _invoke("decision", "accept", "2", "--path", str(root), *extra)


def test_accept_makes_the_draft_stable_and_changes_nothing_else(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    before = (root / DRAFT).read_text()

    result = _accept(root)

    assert result.exit_code == 0, result.output
    assert front_matter(root / DRAFT)["status"] == "stable"
    assert (root / DRAFT).read_text() == before.replace(
        "status: draft\n", "status: stable\n"
    )
    assert "Next: kmctl check --no-drafts" in result.output
    assert okf_validate(root / ".okf").returncode == 0


def test_accept_logs_the_person_from_git(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    _accept(root)

    log = (root / ".okf/log.md").read_text()
    assert log.rstrip().endswith(
        "- Accepted `decisions/0002-use-a-queue` (human:ada@example.com)."
    )


def test_by_names_the_person(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _accept(root, "--by", "human:jasper", "--json")

    assert json.loads(result.stdout) == {
        "id": "decisions/0002-use-a-queue",
        "path": DRAFT,
        "by": "human:jasper",
    }
    assert "(human:jasper)." in (root / ".okf/log.md").read_text()


def test_refuses_without_a_person(tmp_path: Path) -> None:
    root = _repo(tmp_path, email=None)
    before = (root / DRAFT).read_text()

    result = CliRunner(
        env={"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
    ).invoke(app, ["decision", "accept", "2", "--path", str(root)])

    assert result.exit_code == 1
    assert "give --by human:<id>" in result.stderr
    assert (root / DRAFT).read_text() == before


def test_refuses_an_agent_as_the_person(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _accept(root, "--by", "claude-opus/5.5")

    assert result.exit_code == 1
    assert "only a person accepts" in result.stderr
    assert front_matter(root / DRAFT)["status"] == "draft"


def test_refuses_a_record_that_is_not_a_draft(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _accept(root)
    log = (root / ".okf/log.md").read_text()

    result = _accept(root)

    assert result.exit_code == 1
    assert "has status stable, not draft" in result.stderr
    assert (root / ".okf/log.md").read_text() == log


def test_refuses_a_missing_record(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _invoke("decision", "accept", "9", "--path", str(root))

    assert result.exit_code == 1
    assert "no decision 0009" in result.stderr


def test_check_no_drafts_fails_until_the_draft_is_accepted(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    plain = _invoke("check", "--path", str(root))
    strict = _invoke("check", "--path", str(root), "--no-drafts", "--json")
    _accept(root)
    after = _invoke("check", "--path", str(root), "--no-drafts")

    assert plain.exit_code == 0, plain.output
    assert strict.exit_code == 1
    [finding] = [f for f in json.loads(strict.stdout) if f["check"] == "draft"]
    assert finding["file"] == DRAFT
    assert finding["level"] == "error"
    assert "kmctl decision accept 2" in finding["message"]
    assert after.exit_code == 0, after.output
