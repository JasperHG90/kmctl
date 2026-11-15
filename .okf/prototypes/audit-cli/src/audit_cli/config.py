"""The audit's settings, read from a TOML file (``audit.toml`` by default)."""

import hashlib
import os
import pathlib as plb
import tomllib
from typing import Literal

import platformdirs
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from pydantic_core import ErrorDetails

DEFAULT_CONFIG_NAME = "audit.toml"
APP_NAME = "audit-cli"


class _Strict(BaseModel):
    """A settings table that refuses keys it does not know."""

    # A misspelt key is an error, not a setting that silently does nothing.
    model_config = ConfigDict(extra="forbid")


class FilesConfig(_Strict):
    """Which code files the later, code-reading stages read; claim extraction does not use it.

    Git decides first: anything git ignores is never read.
    """

    include_extensions: list[str] = Field(
        default=[
            ".py",
            ".toml",
            ".yaml",
            ".yml",
            ".jinja",
            ".sh",
            ".bash",
            ".md",
            ".json",
            ".hcl",
            ".tf",
            ".nomad",
            ".tpl",
            ".j2",
            ".go",
            ".js",
            ".mjs",
            ".ts",
            ".tsx",
            ".rs",
            ".java",
            ".rb",
            ".ini",
            ".cfg",
            ".conf",
            ".lua",
            ".sql",
        ],
        description="Read only files with these extensions.",
    )
    exclude_dirs: list[str] = Field(
        default=[".loop", ".claude", ".vscode", ".okf", "docs"],
        description="Folders never read, at any depth. Replaces the default list.",
    )
    extend_exclude_dirs: list[str] = Field(default=[], description="More folders to skip, on top of exclude_dirs.")
    exclude_patterns: list[str] = Field(
        default=["*.pyc", "*.lock", "*.min.js", "README.md", "CLAUDE.md", "AGENTS.md"],
        description="File-name globs never read, such as *.pyc. READMEs and agent notes restate the knowledge, so a "
        "check that read them would prove nothing.",
    )
    extend_exclude_patterns: list[str] = Field(
        default=[], description="More file-name globs, on top of exclude_patterns."
    )

    @property
    def skipped_dirs(self) -> list[str]:
        """The folders skipped: exclude_dirs plus extend_exclude_dirs."""
        return list(dict.fromkeys(self.exclude_dirs + self.extend_exclude_dirs))

    @property
    def skipped_patterns(self) -> list[str]:
        """The file-name globs skipped: exclude_patterns plus extend_exclude_patterns."""
        return list(dict.fromkeys(self.exclude_patterns + self.extend_exclude_patterns))


class ChunkingConfig(_Strict):
    """How the bundle is cut into chunks."""

    skip_names: list[str] = Field(default=["index.md", "log.md"], description="Bundle files that are not concepts.")
    skip_dirs: list[str] = Field(default=["prototypes"], description="Bundle folders not to chunk.")
    earlier_sentences: int = Field(default=40, ge=0, description="Sentences of earlier sections shown with each chunk.")


class ProviderConfig(_Strict):
    """An OpenAI-compatible endpoint."""

    base_url: str = Field(description="The endpoint's base URL, ending in /v1.")
    api_key_env: str = Field(description="The environment variable that holds the key.")

    def api_key(self) -> str:
        """Return the key from the environment.

        Raises
        ------
        ConfigError
            If the variable is not set.
        """
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ConfigError(f"the environment variable {self.api_key_env} is not set (the provider's api_key_env)")
        return key


class AgentConfig(_Strict):
    """One model, on one provider, with its call settings."""

    provider: str = Field(description="A name under [providers].")
    model: str = Field(default="", description="The model name the provider expects; required before use.")
    temperature: float = Field(default=0, description="Sampling temperature; 0 keeps runs steady.")
    timeout: float = Field(default=120, description="Seconds before one call gives up.")
    max_retries: int = Field(default=3, description="Retries the client makes on a failed call.")
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(
        default=None,
        description="How much a reasoning model thinks before it answers; unset sends nothing (the model's default).",
    )


class ClaimsConfig(_Strict):
    """Which runs extract claims from each chunk."""

    runs: list[str] = Field(
        default=["extractor", "extractor@2"],
        description=(
            "Extraction runs per chunk, in order: an agent name, optionally with @salt for a second run of the same "
            "agent. The first run's claims stand; each later run adds claims for sentences the runs before it skipped."
        ),
    )


class ChecksConfig(_Strict):
    """How claims are turned into checks: steps that later run against the code with no model."""

    writer: str = Field(default="extractor", description="The agent under [agents] that writes the checks.")
    group_size: int = Field(
        default=6, ge=1, description="The most claims written in one call; claims that read the same file go together."
    )
    fix: bool = Field(
        default=True,
        description="Send each group's failing checks back once, with what their steps saw, before storing them.",
    )
    max_lines_chars: int = Field(
        default=6000, ge=500, description="The most characters of repository lines shown for one claim."
    )
    agent: bool = Field(
        default=False,
        description="Hand the checks the two calls leave failing or unanswered to a searching agent: more checks hold, "
        "at several times the tokens.",
    )
    agent_batch: int = Field(default=4, ge=1, description="Claims per agent batch.")
    agent_max_turns: int = Field(default=20, ge=2, description="Model calls per agent batch.")
    agent_max_tokens: int = Field(default=120_000, ge=1000, description="Input plus output tokens per agent batch.")


class DecisionProviderConfig(_Strict):
    """A decision endpoint: it takes {model, state, questions} and answers each question by name."""

    base_url: str = Field(
        description="The endpoint's URL, such as https://api.typesafe.ai/v1/systemone (Jev) or a gateway's "
        "/v1/decisions (Clef)."
    )
    api_key_env: str = Field(description="The environment variable that holds the key.")

    def api_key(self, name: str) -> str:
        """Return the key from the environment.

        Raises
        ------
        ConfigError
            If the variable is not set.
        """
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ConfigError(
                f"the environment variable {self.api_key_env} is not set (decisions.providers.{name}.api_key_env)"
            )
        return key


class DecisionQuestionConfig(_Strict):
    """One question the decision model is asked: on or off, and which provider and model answer it."""

    enabled: bool = Field(default=False, description="Ask this question.")
    provider: str = Field(default="", description="A name under [decisions.providers].")
    model: str = Field(default="", description="The decision model the provider expects, such as jev-latest.")


QUESTIONS = {
    "failure": "a check failed: does what it saw show the claim is false (drift), or is the check wrong?",
    "judge": "a claim has only a reason: do the lines found for it show it true, false, or neither?",
    "link": "does a check test what its claim says, or only a keyword or a nearby fact?",
}


class DecisionsConfig(_Strict):
    """The decision model's questions, each switched on or off with its own provider and model. All off by default."""

    providers: dict[str, DecisionProviderConfig] = Field(default_factory=dict, description="Decision endpoints.")
    failure: DecisionQuestionConfig = Field(default_factory=DecisionQuestionConfig, description=QUESTIONS["failure"])
    judge: DecisionQuestionConfig = Field(default_factory=DecisionQuestionConfig, description=QUESTIONS["judge"])
    link: DecisionQuestionConfig = Field(default_factory=DecisionQuestionConfig, description=QUESTIONS["link"])
    timeout: float = Field(default=60, description="Seconds before one call gives up.")
    max_calls: int = Field(default=4, ge=1, description="Decision calls in flight at once.")

    def question(self, name: str) -> DecisionQuestionConfig:
        """Return one question's settings by name: failure, judge or link."""
        return {"failure": self.failure, "judge": self.judge, "link": self.link}[name]

    @property
    def enabled(self) -> list[str]:
        """The questions switched on."""
        return [name for name in QUESTIONS if self.question(name).enabled]

    @model_validator(mode="after")
    def _enabled_questions_resolve(self) -> "DecisionsConfig":
        """Check that each question switched on names a provider that exists and a model."""
        for name in self.enabled:
            question = self.question(name)
            if question.provider not in self.providers:
                raise ValueError(
                    f"decisions.{name}.provider is {question.provider!r}, which is not under [decisions.providers]"
                )
            if not question.model.strip():
                raise ValueError(f"decisions.{name} is enabled but sets no model")
        return self


class ConcurrencyConfig(_Strict):
    """Bounds on work in flight."""

    max_model_calls: int = Field(
        default=12, ge=1, description="The most model calls in flight at once, across all runs."
    )


class DatabaseConfig(_Strict):
    """Where the project's SQLite database lives.

    By default it sits in the user's data folder (platformdirs), one folder per
    project: ``<data dir>/audit-cli/projects/<key>/audit.sqlite``.
    """

    path: plb.Path | None = Field(
        default=None, description="A fixed SQLite file, relative to the config file; overrides the data folder."
    )
    project_key: str | None = Field(
        default=None,
        description="The project's folder name in the data folder. Default: the repository's folder name plus a hash "
        "of its full path, so two checkouts never share a database. Set it to keep the database after a move.",
    )


class LoggingConfig(_Strict):
    """Where the CLI writes its log: one JSON object per line, one file per project."""

    level: Literal["debug", "info", "warning", "error"] = Field(default="info", description="The lowest level kept.")
    path: plb.Path | None = Field(
        default=None,
        description="A fixed log file, relative to the config file. Default: <log dir>/audit-cli/<project key>.log "
        "in your user log folder (platformdirs).",
    )


def _default_providers() -> dict[str, ProviderConfig]:
    """Return the provider the defaults use: OpenAI's endpoint, keyed by OPENAI_API_KEY."""
    return {"openai": ProviderConfig(base_url="https://api.openai.com/v1", api_key_env="OPENAI_API_KEY")}


def _default_agents() -> dict[str, AgentConfig]:
    """Return the agent the default runs use; its model has no default and must be set."""
    return {"extractor": AgentConfig(provider="openai")}


class ConfigError(ValueError):
    """The config file is missing, unreadable or inconsistent."""


class TelemetryConfig(_Strict):
    """Whether model calls are traced to LangSmith."""

    enabled: bool = Field(
        default=True,
        description="Turn LangSmith tracing on or off. Everything else comes from LangSmith's own environment "
        "variables: LANGSMITH_API_KEY, and LANGSMITH_PROJECT or LANGSMITH_AGENT_ID with LANGSMITH_AGENT_ENVIRONMENT.",
    )


class Config(_Strict):
    """Every setting, with paths resolved from the config file's folder."""

    files: FilesConfig = FilesConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    providers: dict[str, ProviderConfig] = Field(default_factory=_default_providers)
    agents: dict[str, AgentConfig] = Field(default_factory=_default_agents)
    claims: ClaimsConfig = ClaimsConfig()
    checks: ChecksConfig = ChecksConfig()
    decisions: DecisionsConfig = DecisionsConfig()
    concurrency: ConcurrencyConfig = ConcurrencyConfig()
    database: DatabaseConfig = DatabaseConfig()
    logging: LoggingConfig = LoggingConfig()
    telemetry: TelemetryConfig = TelemetryConfig()
    source: plb.Path | None = Field(default=None, exclude=True, description="The file read; None for the defaults.")
    base_dir: plb.Path = Field(
        default=plb.Path("."), exclude=True, description="The config file's folder; paths resolve from it."
    )

    @model_validator(mode="after")
    def _names_resolve(self) -> "Config":
        """Check that every agent's provider and every run's agent exist."""
        for name, agent in self.agents.items():
            if agent.provider not in self.providers:
                raise ValueError(f"agents.{name}.provider is {agent.provider!r}, which is not under [providers]")
        if len(set(self.claims.runs)) != len(self.claims.runs):
            raise ValueError("claims.runs names a run twice; give a repeat its own salt, such as extractor@2")
        for run in self.claims.runs:
            if run.partition("@")[0] not in self.agents:
                raise ValueError(f"claims.runs names {run!r}, but there is no [agents.{run.partition('@')[0]}]")
        if self.checks.writer not in self.agents:
            raise ValueError(f"checks.writer is {self.checks.writer!r}, but there is no [agents.{self.checks.writer}]")
        return self

    def unset_models(self) -> list[str]:
        """Return the agents the runs use whose model is not set yet."""
        names = dict.fromkeys(run.partition("@")[0] for run in self.claims.runs)
        return [name for name in names if not self.agents[name].model.strip()]

    def project_key(self, root: plb.Path) -> str:
        """Return the project's folder name in the data folder: set, or the root's name plus a hash of its path."""
        if self.database.project_key:
            return self.database.project_key
        return f"{root.name}-{hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:12]}"

    def database_path(self, root: plb.Path) -> plb.Path:
        """Return the SQLite file for the project at ``root``: the configured path, or its file in the data folder."""
        if self.database.path is not None:
            return (self.base_dir / self.database.path).resolve()
        data = plb.Path(os.environ.get("AUDIT_CLI_DATA_DIR") or platformdirs.user_data_dir(APP_NAME, appauthor=False))
        return data / "projects" / self.project_key(root) / "audit.sqlite"

    def log_path(self, root: plb.Path) -> plb.Path:
        """Return the log file for the project at ``root``: the configured path, or its file in the log folder."""
        if self.logging.path is not None:
            return (self.base_dir / self.logging.path).resolve()
        logs = plb.Path(os.environ.get("AUDIT_CLI_LOG_DIR") or platformdirs.user_log_dir(APP_NAME, appauthor=False))
        return logs / f"{self.project_key(root)}.log"


def load_config(path: plb.Path | None, search: list[plb.Path] | None = None) -> Config:
    """Read the config file: ``path``, else the first audit.toml in ``search``, else the built-in defaults.

    Raises
    ------
    ConfigError
        If the file is missing, not TOML, or holds an unknown or inconsistent setting.
    """
    if path is None:
        found = [folder / DEFAULT_CONFIG_NAME for folder in search or [] if (folder / DEFAULT_CONFIG_NAME).is_file()]
        if not found:
            return Config(base_dir=plb.Path.cwd())
        path = found[0]
    try:
        data = tomllib.loads(path.read_text())
    except FileNotFoundError as error:
        raise ConfigError(f"no config file at {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path} is not valid TOML: {error}") from error
    try:
        return Config.model_validate({**data, "base_dir": path.resolve().parent, "source": path.resolve()})
    except ValidationError as error:
        problems = "; ".join(_explain(e) for e in error.errors())
        raise ConfigError(f"{path}: {problems}. `audit init --force` writes a fresh file with every setting") from error


# Settings an older audit.toml may still hold, and what took their place.
REMOVED = {
    "repository": "the path given to audit claims says what to audit",
}


def _explain(error: ErrorDetails) -> str:
    """Return one validation error as a sentence naming the setting."""
    where = ".".join(str(part) for part in error["loc"])
    if error["type"] == "extra_forbidden" and where in {
        "decisions.base_url",
        "decisions.api_key_env",
        "decisions.model",
    }:
        return (
            f"`{where}` moved: name the endpoint under [decisions.providers.NAME] (base_url, api_key_env) and switch "
            "each question on under [decisions.failure], [decisions.judge] and [decisions.link] (enabled, provider, "
            "model)"
        )
    if error["type"] == "extra_forbidden":
        top = str(error["loc"][0])
        if top in REMOVED:
            return f"[{top}] is no longer a setting ({REMOVED[top]}); delete it"
        return f"`{where}` is not a setting; check the spelling or delete it"
    if error["type"] == "missing":
        return f"`{where}` is required"
    message = error["msg"].removeprefix("Value error, ")
    return f"`{where}`: {message}" if where else message


DEFAULT_TOML = """\
# Settings for the audit CLI. Paths are relative to this file. The CLI looks for audit.toml
# in the repository root, then the current folder, unless -c names one.

[files]
# Which code files the code-reading stages read (claim extraction does not use these).
# Git decides first: a file git ignores is never read. Then these apply.
include_extensions = [".py", ".toml", ".yaml", ".yml", ".jinja", ".sh", ".bash", ".md", ".json",
                      ".hcl", ".tf", ".nomad", ".tpl", ".j2", ".go", ".js", ".mjs", ".ts", ".tsx",
                      ".rs", ".java", ".rb", ".ini", ".cfg", ".conf", ".lua", ".sql"]
exclude_dirs = [".loop", ".claude", ".vscode", ".okf", "docs"]
extend_exclude_dirs = []
exclude_patterns = ["*.pyc", "*.lock", "*.min.js", "README.md", "CLAUDE.md", "AGENTS.md"]
extend_exclude_patterns = []

[chunking]
skip_names = ["index.md", "log.md"]
skip_dirs = ["prototypes"]
earlier_sentences = 40

# Any OpenAI-compatible endpoint (OpenAI, a gateway, a local server). The key comes from the named
# environment variable, or a .env file. Add more [providers.NAME] tables to mix endpoints.
[providers.openai]
base_url = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"

[agents.extractor]
provider = "openai"
model = ""             # required: the model name your provider expects
temperature = 0
timeout = 120          # seconds per call
max_retries = 3
# reasoning_effort = "low"   # low, medium or high for a reasoning model; unset sends nothing

[claims]
# Runs per section, in order. The first run's claims stand; each later run adds claims for the
# sentences the runs before it skipped. "agent@salt" runs an agent again as a separate run.
runs = ["extractor", "extractor@2"]

[checks]
# Claims become checks: steps that run against the code with no model. A check is written once and
# written again only when its claim or a file it reads changes.
writer = "extractor"   # the agent under [agents] that writes the checks
group_size = 6         # most claims per call; claims that read the same file go together
fix = true             # send each group's failing checks back once, with what their steps saw
max_lines_chars = 6000 # most characters of repository lines shown for one claim
agent = false          # hand what the two calls leave failing to a searching agent (several times the tokens)
agent_batch = 4
agent_max_turns = 20
agent_max_tokens = 120000

[decisions]
# A decision model answers typed questions with probabilities. Each question below is off until you
# switch it on and name a provider and model for it. A key is needed only for providers in use.
timeout = 60
max_calls = 4          # decision calls in flight at once

# [decisions.providers.typesafe]
# base_url = "https://api.typesafe.ai/v1/systemone"
# api_key_env = "TYPESAFE_API_KEY"

[decisions.failure]    # a check failed: drift, or a wrong check? (audit checks rewrites wrong ones)
enabled = false
# provider = "typesafe"
# model = "jev-latest"

[decisions.judge]      # a claim with only a reason: do its lines show it true or false?
enabled = false

[decisions.link]       # does a check test what its claim says? (audit checks list --status weak)
enabled = false

[concurrency]
max_model_calls = 12   # model calls in flight at once, across all runs

[database]
# The database lives in your data folder, one folder per project, by default.
# project_key = "my-repo"         # name the project's folder; keeps the database after a move
# path = ".audit/audit.sqlite"    # or use a fixed file instead, relative to this file

[logging]
level = "info"         # debug, info, warning or error
# path = "audit.log"   # a fixed file; by default each project logs to your user log folder

[telemetry]
# Trace model calls to LangSmith: true or false. The rest comes from LangSmith's own environment variables,
# in your shell or a .env file: LANGSMITH_API_KEY, and LANGSMITH_PROJECT or LANGSMITH_AGENT_ID + LANGSMITH_AGENT_ENVIRONMENT.
enabled = true
"""
