"""Tests for reading audit.toml."""

import hashlib
import pathlib as plb

import pytest

from audit_cli.config import DEFAULT_TOML, Config, ConfigError, load_config


def test_the_default_toml_reads_back_as_the_defaults(tmp_path: plb.Path) -> None:
    """The file audit init writes holds the same settings as the built-in defaults."""
    (tmp_path / "audit.toml").write_text(DEFAULT_TOML)
    config = load_config(tmp_path / "audit.toml")
    assert config.model_dump(exclude={"base_dir"}) == Config().model_dump(exclude={"base_dir"})


def test_a_misspelt_key_is_refused(tmp_path: plb.Path) -> None:
    """An unknown key names the problem instead of being ignored."""
    (tmp_path / "audit.toml").write_text("[files]\ninclude_extension = ['.py']\n")
    with pytest.raises(ConfigError, match="include_extension"):
        load_config(tmp_path / "audit.toml")


@pytest.mark.parametrize(
    ("toml", "message"),
    [
        ('[claims]\nruns = ["nobody"]\n', "no \\[agents.nobody\\]"),
        ('[agents.extractor]\nprovider = "nowhere"\nmodel = "m"\n', "not under \\[providers\\]"),
        ('[claims]\nruns = ["extractor", "extractor"]\n', "names a run twice"),
    ],
)
def test_names_must_resolve(tmp_path: plb.Path, toml: str, message: str) -> None:
    """A run must name an agent, and an agent a provider."""
    (tmp_path / "audit.toml").write_text(toml)
    with pytest.raises(ConfigError, match=message):
        load_config(tmp_path / "audit.toml")


def test_extend_lists_add_to_the_defaults(tmp_path: plb.Path) -> None:
    """extend_exclude_dirs and extend_exclude_patterns add to the lists, not replace them."""
    (tmp_path / "audit.toml").write_text(
        '[files]\nextend_exclude_dirs = ["vendor"]\nextend_exclude_patterns = ["*.gen.py"]\n'
    )
    files = load_config(tmp_path / "audit.toml").files
    assert "vendor" in files.skipped_dirs and ".okf" in files.skipped_dirs
    assert "*.gen.py" in files.skipped_patterns and "*.pyc" in files.skipped_patterns


def test_the_database_sits_in_the_data_folder_under_a_project_key(tmp_path: plb.Path, data_dir: plb.Path) -> None:
    """By default each project gets its own folder, named for the repository and a hash of its path."""
    digest = hashlib.sha256(str(tmp_path.resolve()).encode()).hexdigest()[:12]
    assert Config().database_path(tmp_path) == data_dir / "projects" / f"{tmp_path.name}-{digest}" / "audit.sqlite"


def test_a_project_key_or_a_path_overrides_the_default(tmp_path: plb.Path, data_dir: plb.Path) -> None:
    """project_key names the folder; path picks a fixed file relative to the config file."""
    (tmp_path / "audit.toml").write_text('[database]\nproject_key = "kmctl"\n')
    config = load_config(tmp_path / "audit.toml")
    assert config.database_path(tmp_path) == data_dir / "projects" / "kmctl" / "audit.sqlite"
    (tmp_path / "audit.toml").write_text('[database]\npath = "db/audit.sqlite"\n')
    config = load_config(tmp_path / "audit.toml")
    assert config.database_path(tmp_path) == (tmp_path / "db" / "audit.sqlite").resolve()


def test_the_config_is_found_in_the_first_search_folder_that_has_one(tmp_path: plb.Path) -> None:
    """Without -c, the first folder in the search list that holds audit.toml wins."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "audit.toml").write_text("[concurrency]\nmax_model_calls = 3\n")
    config = load_config(None, search=[tmp_path / "a", tmp_path / "b"])
    assert config.concurrency.max_model_calls == 3


def test_a_missing_key_variable_is_named(monkeypatch: pytest.MonkeyPatch) -> None:
    """The provider's key comes from its variable, and a missing one says which."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        Config().providers["openai"].api_key()


def test_the_defaults_name_no_model() -> None:
    """The built-in defaults and audit init leave the model to the user."""
    assert Config().unset_models() == ["extractor"]


@pytest.mark.parametrize(
    ("toml", "message"),
    [
        ("[repository]\nroot = '.'\n", "[repository] is no longer a setting"),
        ("[telemetry]\nproject = 'p'\n", "`telemetry.project` is not a setting"),
        ("[files]\nexclude_dir = []\n", "`files.exclude_dir` is not a setting"),
        ("[concurrency]\nmax_model_calls = 0\n", "`concurrency.max_model_calls`"),
    ],
)
def test_config_errors_name_the_setting_in_plain_words(tmp_path: plb.Path, toml: str, message: str) -> None:
    """A bad setting is named and explained, with no pydantic dump, and the fix is offered."""
    (tmp_path / "audit.toml").write_text(toml)
    with pytest.raises(ConfigError) as caught:
        load_config(tmp_path / "audit.toml")
    assert message in str(caught.value) and "audit init --force" in str(caught.value)
    assert "pydantic" not in str(caught.value)


@pytest.mark.parametrize(
    ("toml", "message"),
    [
        (
            '[decisions.link]\nenabled = true\nprovider = "nowhere"\nmodel = "m"\n',
            "not under \\[decisions.providers\\]",
        ),
        (
            '[decisions.providers.t]\nbase_url = "u"\napi_key_env = "K"\n[decisions.failure]\nenabled = true\nprovider = "t"\n',
            "sets no model",
        ),
        ('[decisions]\nbase_url = "u"\nmodel = "m"\n', "moved: name the endpoint under \\[decisions.providers.NAME\\]"),
    ],
)
def test_each_decision_question_names_its_provider_and_model(tmp_path: plb.Path, toml: str, message: str) -> None:
    """A question switched on needs a provider that exists and a model; the old single endpoint says where it moved."""
    (tmp_path / "audit.toml").write_text(toml)
    with pytest.raises(ConfigError, match=message):
        load_config(tmp_path / "audit.toml")


def test_questions_are_off_until_switched_on(tmp_path: plb.Path) -> None:
    """With no [decisions] settings no question is asked; switching one on needs only that question's provider."""
    assert Config().decisions.enabled == []
    (tmp_path / "audit.toml").write_text(
        '[decisions.providers.t]\nbase_url = "u"\napi_key_env = "K"\n[decisions.link]\nenabled = true\nprovider = "t"\n'
        'model = "jev-latest"\n'
    )
    assert load_config(tmp_path / "audit.toml").decisions.enabled == ["link"]
