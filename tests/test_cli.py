from typer.testing import CliRunner

from kmctl import app


def test_version_prints_the_package_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.startswith("kmctl ")
