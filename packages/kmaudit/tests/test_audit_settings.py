"""The per-user audit.toml: where it is read from, off by default, and refusals that name the key."""

from pathlib import Path

import pytest
from kmaudit import AuditError
from kmaudit.settings import api_key, load, settings_path

ON = """
[decisions.providers.clef]
base_url = "https://gateway.example/v1/decisions"
api_key_env = "CLEF_TEST_KEY"

[decisions.failure]
enabled = true
provider = "clef"
model = "jev-latest"
"""


@pytest.fixture(autouse=True)
def _home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("KMCTL_AUDIT_CONFIG", raising=False)
    monkeypatch.delenv("CLEF_TEST_KEY", raising=False)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_xdg_path_and_the_home_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert settings_path() == tmp_path / "xdg" / "kmctl" / "audit.toml"
    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert settings_path() == tmp_path / "home" / ".config" / "kmctl" / "audit.toml"


def test_config_and_the_variable_win(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path / "xdg" / "kmctl" / "audit.toml", "")
    env = _write(tmp_path / "env.toml", ON)
    given = _write(tmp_path / "given.toml", "")
    monkeypatch.setenv("KMCTL_AUDIT_CONFIG", str(env))

    assert load().decisions.failure.enabled
    assert not load(given).decisions.failure.enabled


def test_every_question_is_off_with_no_file() -> None:
    settings = load()

    assert settings.source is None
    assert not any(
        settings.decisions.question(q).enabled for q in ("failure", "claim", "link")
    )


def test_a_named_file_that_is_missing_refuses(tmp_path: Path) -> None:
    with pytest.raises(AuditError, match="does not exist"):
        load(tmp_path / "nope.toml")


@pytest.mark.parametrize(
    ("text", "names"),
    [
        ("[decisions]\nmax_call = 2\n", "decisions.max_call: unknown key"),
        (
            ON.replace('provider = "clef"', 'provider = "other"'),
            "decisions.failure.provider",
        ),
        (ON.replace('model = "jev-latest"', 'model = ""'), "decisions.failure.model"),
    ],
    ids=["misspelt", "unknown-provider", "no-model"],
)
def test_bad_settings_refuse_naming_the_key(
    tmp_path: Path, text: str, names: str
) -> None:
    with pytest.raises(AuditError, match=names.replace(".", r"\.")):
        load(_write(tmp_path / "audit.toml", text))


def test_a_missing_key_variable_names_the_variable_not_a_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = load(_write(tmp_path / "audit.toml", ON))

    with pytest.raises(AuditError, match="CLEF_TEST_KEY"):
        api_key(settings, "clef")
    monkeypatch.setenv("CLEF_TEST_KEY", "sk-secret-value")
    assert api_key(settings, "clef") == "sk-secret-value"
