"""Per-user settings for ``kmaudit judge``: which decision questions are on, and who answers them.

The file is ``$XDG_CONFIG_HOME/kmctl/audit.toml`` (``~/.config/kmctl/audit.toml``
when the variable is unset), or the file ``--config`` or
``KMCTL_AUDIT_CONFIG`` names. With no file, every question is off. A key is
read only from the variable a provider's ``api_key_env`` names, and never
printed.
"""

import os
import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from kmaudit import AuditError

ENV = "KMCTL_AUDIT_CONFIG"
Question = Literal["failure", "claim", "link"]
QUESTIONS: tuple[Question, ...] = ("failure", "claim", "link")
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_CALLS = 4


class _Strict(BaseModel):
    """A settings table that refuses an unknown key, so a typo fails loudly."""

    model_config = ConfigDict(extra="forbid")


class Provider(_Strict):
    """A decision endpoint: it takes {model, state, questions} and answers each question by name."""

    base_url: str = Field(
        description="The endpoint, such as a gateway's /v1/decisions."
    )
    api_key_env: str = Field(description="The environment variable that holds the key.")


class QuestionSettings(_Strict):
    """One question: on or off, and which provider and model answer it."""

    enabled: bool = Field(default=False, description="Ask this question.")
    provider: str = Field(default="", description="A name under [decisions.providers].")
    model: str = Field(
        default="", description="The decision model the provider expects."
    )


class Decisions(_Strict):
    """The ``[decisions]`` table: providers, the three questions, a timeout and a bound on calls in flight."""

    providers: dict[str, Provider] = Field(default_factory=dict)
    failure: QuestionSettings = Field(default_factory=QuestionSettings)
    claim: QuestionSettings = Field(default_factory=QuestionSettings)
    link: QuestionSettings = Field(default_factory=QuestionSettings)
    timeout: float = Field(
        default=DEFAULT_TIMEOUT_SECONDS, gt=0, description="Seconds one call may take."
    )
    max_calls: int = Field(
        default=DEFAULT_MAX_CALLS, ge=1, description="Calls in flight at once."
    )

    @model_validator(mode="after")
    def _named(self) -> "Decisions":
        """Refuse a question switched on without a known provider and a model."""
        for name in QUESTIONS:
            q: QuestionSettings = getattr(self, name)
            if not q.enabled:
                continue
            if q.provider not in self.providers:
                raise ValueError(
                    f"decisions.{name}.provider is {q.provider!r}, which is not under [decisions.providers]"
                )
            if not q.model.strip():
                raise ValueError(
                    f"decisions.{name} is enabled but decisions.{name}.model is not set"
                )
        return self

    def question(self, name: Question) -> QuestionSettings:
        """The settings of one question."""
        settings: QuestionSettings = getattr(self, name)
        return settings


class Settings(_Strict):
    """The whole audit.toml."""

    decisions: Decisions = Field(default_factory=Decisions)
    source: Path | None = Field(
        default=None,
        exclude=True,
        description="The file read; None when there is none.",
    )


def settings_path(given: Path | None = None) -> Path:
    """The settings file: ``given``, else ``KMCTL_AUDIT_CONFIG``, else the XDG config folder's kmctl/audit.toml."""
    if given is not None:
        return given
    if os.environ.get(ENV):
        return Path(os.environ[ENV])
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "kmctl" / "audit.toml"


def load(given: Path | None = None) -> Settings:
    """Read the settings; with no file at the default place, every question is off.

    Raises
    ------
    AuditError
        When a named file is missing, the file is not TOML, or a key is unknown or wrong, naming the key.
    """
    path = settings_path(given)
    if not path.is_file():
        if given is not None or os.environ.get(ENV):
            raise AuditError(
                f"settings file {path} does not exist; create it or drop --config / {ENV}"
            )
        return Settings()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise AuditError(f"{path} is not TOML ({error}); fix it") from error
    try:
        settings = Settings.model_validate(data)
    except ValidationError as error:
        first = error.errors()[0]
        where = ".".join(str(p) for p in first["loc"] if p != "__root__")
        message = first["msg"].removeprefix("Value error, ")
        what = "unknown key" if first["type"] == "extra_forbidden" else message
        raise AuditError(
            f"{path}: {where}: {what}; fix it"
            if where
            else f"{path}: {message}; fix it"
        ) from error
    return settings.model_copy(update={"source": path})


def api_key(settings: Settings, provider: str) -> str:
    """The key of a provider, read from the variable its ``api_key_env`` names.

    Raises
    ------
    AuditError
        When the variable is not set, naming the variable and never a value.
    """
    env = settings.decisions.providers[provider].api_key_env
    key = os.environ.get(env, "")
    if not key:
        raise AuditError(
            f"the environment variable {env} is not set (decisions.providers.{provider}.api_key_env); set it"
        )
    return key
