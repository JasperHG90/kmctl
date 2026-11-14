"""The anchors of a claim and the lines a check writer is shown for it."""

import sys
from pathlib import Path

import pytest
from kmaudit.anchors import Evidence, claim_commands, resolve
from kmaudit.lines import LineFinder
from kmaudit.steps import Repository

from .fixtures.audit_repo import make_repo


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return Repository(make_repo(tmp_path / "repo"))


def _find(repo: Repository, claim: str, concept_text: str = "") -> tuple[list, object]:
    evidence = Evidence(repo, walk_help=False)
    spans = [s for s in claim.split("`")[1::2]]
    anchors = [resolve(evidence, s, claim_commands(evidence, spans)) for s in spans]
    return anchors, LineFinder(repo).find(claim, claim, anchors, concept_text, [])


@pytest.mark.parametrize(
    ("claim", "kind", "status", "shown"),
    [
        ("`ci/audit.yml` runs on ubuntu.", "path", "present", "runs-on: ubuntu-latest"),
        (
            "`scripts/release.py --fast` skips the slow checks.",
            "command",
            "found",
            "--fast",
        ),
        ("Retries stop after `MAX_RETRIES`.", "name", "defined", "MAX_RETRIES = 3"),
    ],
    ids=["path", "flag", "python-name"],
)
def test_each_anchor_gets_the_lines_around_it(
    repo: Repository, claim: str, kind: str, status: str, shown: str
) -> None:
    anchors, lines = _find(repo, claim)

    assert (anchors[0].kind, anchors[0].status) == (kind, status)
    assert lines.source == "anchors"
    assert shown in lines.text


def test_a_claim_naming_nothing_gets_keyword_windows_from_its_sources(
    repo: Repository,
) -> None:
    concept = (
        "---\ntype: architecture\nsources:\n  - resource: src/tool.py\n---\n\n# Tool\n"
    )

    anchors, lines = _find(
        repo, "The main function calls exit when argv is long.", concept
    )

    assert anchors == []
    assert lines.source == "area"
    assert lines.files == ["src/tool.py"]
    assert "sys.exit(1)" in lines.text


def test_python_definitions_resolve_without_the_extra(
    repo: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "ast_grep_py", None)
    monkeypatch.setitem(sys.modules, "jmespath", None)

    anchors, _ = _find(repo, "`main` writes the file.")

    assert (anchors[0].status, anchors[0].where) == ("defined", ["src/tool.py"])


def test_an_unknown_name_is_absent(repo: Repository) -> None:
    anchors, _ = _find(repo, "`frobnicate` cleans up.")

    assert anchors[0].status == "absent"
