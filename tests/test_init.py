import json
from pathlib import Path

from conftest import okf_validate
from typer.testing import CliRunner

from kmctl import app

FILES = ("docs/README.md", ".okf/index.md", ".okf/log.md", ".okf/manifesto.md")


def _init(root: Path, *args: str):
    return CliRunner().invoke(app, ["init", "--path", str(root), *args])


def _snapshot(root: Path) -> dict[str, tuple[str, int]]:
    return {f: ((root / f).read_text(), (root / f).stat().st_mtime_ns) for f in FILES}


def test_init_creates_docs_and_bundle(tmp_path: Path) -> None:
    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    for f in FILES:
        assert (tmp_path / f).is_file(), f
        assert f in result.stdout, f


def test_init_twice_changes_nothing(tmp_path: Path) -> None:
    _init(tmp_path)
    before = _snapshot(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert _snapshot(tmp_path) == before
    assert "created" not in result.stdout.lower()


def test_init_keeps_existing_files(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / ".okf").mkdir()
    (tmp_path / "docs" / "README.md").write_text("my docs\n")
    (tmp_path / ".okf" / "manifesto.md").write_text("my manifesto\n")

    _init(tmp_path)

    assert (tmp_path / "docs" / "README.md").read_text() == "my docs\n"
    assert (tmp_path / ".okf" / "manifesto.md").read_text() == "my manifesto\n"


def test_init_bundle_is_conformant(tmp_path: Path) -> None:
    _init(tmp_path)

    check = okf_validate(tmp_path / ".okf")

    assert check.returncode == 0, check.stdout + check.stderr


def test_init_creates_no_empty_folders(tmp_path: Path) -> None:
    _init(tmp_path)

    dirs = [p for p in (tmp_path / "docs").rglob("*") if p.is_dir()]
    dirs += [p for p in (tmp_path / ".okf").rglob("*") if p.is_dir()]
    assert dirs == []


def test_init_json_output(tmp_path: Path) -> None:
    first = json.loads(_init(tmp_path, "--json").stdout)
    second = json.loads(_init(tmp_path, "--json").stdout)

    assert sorted(first["created"]) == sorted(FILES)
    assert first["skipped"] == []
    assert second["created"] == []
    assert sorted(second["skipped"]) == sorted(FILES)


def test_init_refuses_missing_path(tmp_path: Path) -> None:
    missing = tmp_path / "typo"

    result = _init(missing)

    assert result.exit_code != 0
    assert not missing.exists()


def test_init_refuses_file_path(tmp_path: Path) -> None:
    target = tmp_path / "a-file"
    target.write_text("")

    result = _init(target)

    assert result.exit_code != 0
    assert result.exception is None or isinstance(result.exception, SystemExit)


def _partial_bundle(root: Path) -> str:
    (root / ".okf").mkdir()
    index = '---\nokf_version: "0.2"\n---\n\n# Bundle\n'
    (root / ".okf" / "index.md").write_text(index)
    (root / ".okf" / "log.md").write_text("# Log\n")
    return index


def test_init_warns_when_kept_index_misses_new_manifesto(tmp_path: Path) -> None:
    index = _partial_bundle(tmp_path)

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".okf" / "index.md").read_text() == index
    assert "index.md does not link the new manifesto" in result.stderr
    assert "log.md has no line for the new manifesto" in result.stderr


def test_init_json_lists_warnings(tmp_path: Path) -> None:
    _partial_bundle(tmp_path)

    data = json.loads(_init(tmp_path, "--json").stdout)

    assert len(data["warnings"]) == 2


def test_init_no_warning_when_kept_index_already_links_manifesto(
    tmp_path: Path,
) -> None:
    (tmp_path / ".okf").mkdir()
    index = '---\nokf_version: "0.2"\n---\n\n- [Manifesto](manifesto.md): the design.\n'
    (tmp_path / ".okf" / "index.md").write_text(index)
    (tmp_path / ".okf" / "log.md").write_text("# Log\n\n- Wrote `manifesto`.\n")

    result = _init(tmp_path)

    assert result.exit_code == 0, result.output
    assert "warning" not in result.stderr
