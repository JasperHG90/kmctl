"""The section cutter: ids, sentences, fences, corrections, deprecated concepts and change keys."""

from pathlib import Path

import pytest
from kmaudit import AuditError, instructions
from kmaudit.sections import cut, resolve_target, split_headers, split_sentences

from .fixtures.audit_repo import make_repo


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return make_repo(tmp_path / "repo")


def _sections(repo: Path) -> dict:
    return {s.id: s for s in cut(resolve_target(repo))}


def test_section_ids_and_sentences(repo: Path) -> None:
    sections = _sections(repo)

    assert sorted(sections) == [
        "decisions/0001-use-sqlite#correction-2026-01-02",
        "decisions/0001-use-sqlite#decision",
        "tool#parts",
        "tool#values",
    ]
    assert sections["tool#parts"].sentences == [
        "The CLI writes `out.txt`.",
        "It reads `config.toml` on start.",
        "```python\n# not a header\nx = 1\n```",
    ]
    assert sections["tool#parts"].section == "The tool > Parts"


def test_code_fence_is_kept_whole_and_not_a_header() -> None:
    body = "# Top\n\n## A\n\nOne.\n\n```sh\n# comment\n## also not\n```\n"

    parts = split_headers(body)

    assert [name for name, _ in parts] == ["Top > A"]
    assert split_sentences(parts[0][1])[-1] == "```sh\n# comment\n## also not\n```"


def test_short_fragments_join_the_next_sentence() -> None:
    assert split_sentences("- **Note.** The tool writes files.") == [
        "- **Note.** The tool writes files."
    ]


def test_correction_context(repo: Path) -> None:
    sections = _sections(repo)

    decision = sections["decisions/0001-use-sqlite#decision"]
    correction = sections["decisions/0001-use-sqlite#correction-2026-01-02"]
    assert "moved to a folder" in decision.corrections
    assert correction.corrections == ""
    assert correction.is_correction


def test_a_correction_sees_only_the_corrections_after_it(repo: Path) -> None:
    """A later correction that overturns an earlier one is context for it."""
    record = repo / ".okf" / "decisions" / "0001-use-sqlite.md"
    record.write_text(
        record.read_text()
        + "\n## Correction, 2026-03-04\n\nThe store moved back to one file.\n"
    )

    sections = _sections(repo)

    first = sections["decisions/0001-use-sqlite#correction-2026-01-02"]
    last = sections["decisions/0001-use-sqlite#correction-2026-03-04"]
    assert "moved back to one file" in first.corrections
    assert "moved to a folder" not in first.corrections
    assert last.corrections == ""


def test_earlier_sections_are_context(repo: Path) -> None:
    values = _sections(repo)["tool#values"]

    assert "[1.1] The CLI writes `out.txt`." in values.earlier
    assert values.earlier_ids == ["tool#parts"]


def test_deprecated_concepts_index_log_and_prototypes_are_skipped(repo: Path) -> None:
    concepts = {s.concept for s in _sections(repo).values()}

    assert concepts == {"tool", "decisions/0001-use-sqlite"}


def _key(repo: Path, sid: str = "tool#parts") -> str:
    return _sections(repo)[sid].key


def test_keys_are_stable(repo: Path) -> None:
    assert _key(repo) == _key(repo)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("It reads `config.toml` on start.", "It reads `settings.toml` on start."),
        ("title: The tool", "title: The new tool"),
    ],
    ids=["text", "title"],
)
def test_key_moves_with_text_and_title(repo: Path, old: str, new: str) -> None:
    before = _key(repo)
    path = repo / ".okf" / "tool.md"
    path.write_text(path.read_text().replace(old, new))

    assert _key(repo) != before


def test_key_moves_with_the_guidance(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _key(repo)
    monkeypatch.setattr(instructions, "GUIDANCE", instructions.GUIDANCE + " ")

    assert _key(repo) != before


def test_key_stays_when_only_the_way_to_submit_changes(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = _key(repo)
    monkeypatch.setattr(instructions, "SUBMIT", "Call the submit tool instead.")
    monkeypatch.setattr(instructions, "INSTRUCTIONS", "changed")

    assert _key(repo) == before


def test_editing_one_section_leaves_the_others(repo: Path) -> None:
    before = _key(repo, "decisions/0001-use-sqlite#decision")
    path = repo / ".okf" / "tool.md"
    path.write_text(path.read_text().replace("Plain words", "Short words"))

    assert _key(repo, "decisions/0001-use-sqlite#decision") == before


def test_target_forms(repo: Path) -> None:
    assert resolve_target(repo).bundle == (repo / ".okf").resolve()
    assert resolve_target(repo / ".okf").files is None
    one = resolve_target(repo / ".okf" / "tool.md")
    assert one.concepts == {"tool"}
    assert one.root == repo.resolve()


def test_target_refuses_a_folder_with_no_bundle(tmp_path: Path) -> None:
    with pytest.raises(AuditError, match="kmctl init"):
        resolve_target(tmp_path)
