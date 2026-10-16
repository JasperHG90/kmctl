import json
from pathlib import Path

from conftest import plain
from typer.testing import CliRunner

from kmctl import app


def test_version_prints_the_package_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.startswith("kmctl ")


def test_update_is_init_alias(tmp_path: Path) -> None:
    init_root, update_root = tmp_path / "a", tmp_path / "b"
    init_root.mkdir()
    update_root.mkdir()
    runner = CliRunner()

    by_init = runner.invoke(app, ["init", "--path", str(init_root), "--json"])
    by_update = runner.invoke(app, ["update", "--path", str(update_root), "--json"])

    assert by_init.exit_code == by_update.exit_code == 0, by_update.output
    assert json.loads(by_update.stdout) == json.loads(by_init.stdout)

    def tree(root: Path) -> set[str]:
        return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}

    assert tree(update_root) == tree(init_root)
    assert " update " in plain(runner.invoke(app, ["--help"]).stdout)
