import json
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner, Result

from kmctl import app
from kmctl.okf import front_matter

KEY = "0b5c3a8e-1111-2222-3333-444455556666"


def _invoke(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


def _repo(root: Path) -> Path:
    assert _invoke("init", "--path", str(root)).exit_code == 0
    return root


def _handoff(root: Path, title: str, description: str, key: str | None = KEY) -> Result:
    extra = ["--key", key] if key else []
    return _invoke(
        "new",
        "handoff",
        title,
        "--description",
        description,
        "--path",
        str(root),
        "--json",
        *extra,
    )


def test_existing_key_updates_in_place(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    first = json.loads(_handoff(root, "Parser work", "Halfway.").stdout)
    page = root / first["path"]
    page.write_text(page.read_text() + "\nold notes\n")
    before = front_matter(page)
    log_before = (root / ".okf/log.md").read_text().splitlines()

    second = _handoff(root, "Parser work, day two", "Nearly done.")
    after = front_matter(page)
    index = (root / ".okf/handoffs/index.md").read_text()

    assert second.exit_code == 0, second.output
    assert json.loads(second.stdout)["path"] == first["path"]
    assert sorted(p.name for p in (root / ".okf/handoffs").glob("*.md")) == [
        "index.md",
        page.name,
    ]
    assert after["description"] == "Nearly done."
    assert after["handoff_key"] == KEY
    assert "old notes" not in page.read_text()
    assert str(after["generated"]["at"]) >= str(before["generated"]["at"])
    assert after["stale_after"] >= before["stale_after"]
    assert index.count(f"({page.name})") == 1
    assert "Nearly done." in index
    assert len((root / ".okf/log.md").read_text().splitlines()) == len(log_before) + 1


def test_unknown_key_creates_handoff(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _handoff(root, "Parser work", "Halfway.")

    other = json.loads(
        _handoff(root, "Lexer work", "Started.", key="another-session").stdout
    )

    assert front_matter(root / other["path"])["handoff_key"] == "another-session"
    assert len(list((root / ".okf/handoffs").glob("*.md"))) == 3


def test_handoff_bundle_validates(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _handoff(root, "Parser work", "Halfway.")
    _handoff(root, "Parser work again", "Done.")

    check = okf_validate(root / ".okf")

    assert check.returncode == 0, check.stdout + check.stderr
    assert _invoke("check", "--path", str(root)).exit_code == 0


def test_key_only_on_handoffs(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    result = _invoke(
        "new", "decision", "X", "--description", "Y.", "--key", KEY, "--path", str(root)
    )

    assert result.exit_code != 0


def test_repeated_update_logs_once(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _handoff(root, "Parser work", "Halfway.")
    _handoff(root, "Parser work", "Nearly done.")
    log_after_first_update = (root / ".okf/log.md").read_text()

    _handoff(root, "Parser work", "Nearly done, take two.")

    assert (root / ".okf/log.md").read_text() == log_after_first_update


def test_empty_key_is_refused(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    for key in ("", "   "):
        result = _invoke(
            "new",
            "handoff",
            "A work",
            "--description",
            "A.",
            "--key",
            key,
            "--path",
            str(root),
        )
        assert result.exit_code == 1, repr(key)
        assert "--key is empty" in result.stderr

    assert not (root / ".okf/handoffs").exists()


def test_update_on_a_later_day_logs_again(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from kmctl.concepts import new_concept

    root = _repo(tmp_path)
    day1 = datetime(2026, 10, 15, 9, tzinfo=UTC)
    day2 = datetime(2026, 10, 16, 9, tzinfo=UTC)
    new_concept(root, "handoff", "Work", "Start.", now=day1, key=KEY)
    new_concept(root, "handoff", "Work", "More.", now=day1, key=KEY)
    new_concept(root, "handoff", "Work", "Even more.", now=day2, key=KEY)

    log = (root / ".okf/log.md").read_text()

    assert "## 2026-10-16" in log
    assert log.rstrip().endswith(
        "- Updated `handoffs/work` with `kmctl new handoff --key`."
    )
    assert log.count("Updated `handoffs/work`") == 2


def test_update_checks_the_title(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _handoff(root, "Parser work", "Halfway.")

    result = _handoff(root, "!!!", "Bad title.")

    assert result.exit_code == 1
