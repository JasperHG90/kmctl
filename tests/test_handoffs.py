import json
from pathlib import Path

from typer.testing import CliRunner

from kmctl import app


def _handoff(root: Path, name: str, at: str, stale_after: str | None = None) -> None:
    folder = root / ".okf" / "handoffs"
    folder.mkdir(parents=True, exist_ok=True)
    stale = f"stale_after: {stale_after}\n" if stale_after else ""
    (folder / f"{name}.md").write_text(
        f'---\ntype: handoff\ntitle: "Handoff: {name}"\ndescription: "Where {name} stands."\n'
        f"generated:\n  by: claude-opus/5.5\n  at: {at}\n{stale}---\n\n# {name}\n"
    )


def _list(root: Path, *args: str):
    return CliRunner().invoke(app, ["handoffs", "--path", str(root), *args])


def _ids(root: Path) -> list[str]:
    return [h["id"] for h in json.loads(_list(root, "--json").stdout)]


def test_handoffs_order(tmp_path: Path) -> None:
    _handoff(tmp_path, "old", "2026-10-01T09:00:00Z")
    _handoff(tmp_path, "b-tie", "2026-10-10T09:00:00Z")
    _handoff(tmp_path, "a-tie", "2026-10-10T09:00:00Z")
    _handoff(tmp_path, "new", "2026-10-12T09:00:00Z")

    assert _ids(tmp_path) == [
        "handoffs/new",
        "handoffs/a-tie",
        "handoffs/b-tie",
        "handoffs/old",
    ]


def test_handoffs_filtering(tmp_path: Path) -> None:
    _handoff(tmp_path, "expired", "2026-10-01T09:00:00Z", "2020-01-01T00:00:00Z")
    _handoff(tmp_path, "forever", "2026-10-02T09:00:00Z")
    _handoff(tmp_path, "live", "2026-10-03T09:00:00Z", "2999-01-01T00:00:00Z")
    (tmp_path / ".okf" / "handoffs" / "index.md").write_text("# Handoffs\n")

    assert _ids(tmp_path) == ["handoffs/live", "handoffs/forever"]


def test_handoffs_json(tmp_path: Path) -> None:
    _handoff(tmp_path, "one", "2026-10-03T09:00:00Z")

    [entry] = json.loads(_list(tmp_path, "--json").stdout)
    empty = json.loads(_list(tmp_path / ".okf" / "handoffs", "--json").stdout)

    assert entry == {
        "id": "handoffs/one",
        "path": ".okf/handoffs/one.md",
        "title": "Handoff: one",
        "description": "Where one stands.",
        "date": "2026-10-03T09:00:00Z",
    }
    assert empty == []


def test_handoffs_none(tmp_path: Path) -> None:
    result = _list(tmp_path)

    assert result.exit_code == 0, result.output
    assert "no live handoffs" in result.stdout


def test_handoffs_skip_bad_front_matter_with_a_warning(tmp_path: Path) -> None:
    _handoff(tmp_path, "good", "2026-10-03T09:00:00Z")
    folder = tmp_path / ".okf" / "handoffs"
    (folder / "broken.md").write_text("---\ntitle: [bad\n---\n")
    (folder / "odd.md").write_text("---\ntitle: Odd\ngenerated: yesterday\n---\n")

    result = _list(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    assert [h["id"] for h in json.loads(result.stdout)] == [
        "handoffs/good",
        "handoffs/odd",
    ]
    assert "broken.md" in result.stderr


def test_handoffs_dates_are_converted_to_utc(tmp_path: Path) -> None:
    _handoff(tmp_path, "offset", "2026-10-03T09:00:00+02:00")

    [entry] = json.loads(_list(tmp_path, "--json").stdout)

    assert entry["date"] == "2026-10-03T07:00:00Z"


def test_handoffs_skip_non_utf8_file_with_a_warning(tmp_path: Path) -> None:
    _handoff(tmp_path, "good", "2026-10-03T09:00:00Z")
    (tmp_path / ".okf" / "handoffs" / "latin.md").write_bytes(
        b"---\ntitle: caf\xe9\n---\n"
    )

    result = _list(tmp_path, "--json")

    assert result.exit_code == 0, result.output
    assert [h["id"] for h in json.loads(result.stdout)] == ["handoffs/good"]
    assert "latin.md" in result.stderr


def test_has_passed_at_the_exact_instant() -> None:
    from datetime import UTC, datetime

    from kmctl.okf import has_passed

    now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

    assert has_passed("2026-10-15T12:00:00Z", now)
    assert not has_passed("2026-10-15T12:00:01Z", now)
