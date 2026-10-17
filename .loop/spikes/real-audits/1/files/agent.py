# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic-ai-slim[openai]==2.57.0", "pyyaml>=6.0.3"]
# ///
"""A small agent for CI: give it a task, a model, folders to read and skills to use.

Run it with ``uv run action/agent.py run --help``. It needs nothing from kmctl:
by default it audits a repository's knowledge with the skills that sit next to
it in ``apm/.apm/skills``, but ``--prompt`` gives it any other task.

The agent reads the repository, every ``--context`` folder and every
``--skills`` folder, and can run shell commands so it can use the scripts
skills ship. Commands get a clean environment without the API key or a GitHub
token, but run as the same user, so a command could still read the key from
``/proc`` (ADR 0017). It returns a typed report, which ``run`` writes to
``--out`` as ``report.json``, ``report.md`` and ``transcript.json``.

``publish`` posts that report to one GitHub issue with ``gh``. Run it in a
job of its own, which gets the report as an artifact and nothing else from
the agent's job, so nothing the agent changed runs with the token.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# PydanticAI prints a Logfire banner to stderr on import unless this is set.
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

import yaml
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

HERE = Path(__file__).resolve().parent
#: kmctl's skills and agents, in the action's own checkout.
PACKAGE = Path("/home/vscode/kmctl/apm/.apm")
DEFAULT_SKILLS = PACKAGE / "skills"
AUDITOR = PACKAGE / "agents" / "kmctl-auditor.md"

READ_BYTES = 100_000
READ_LINES = 2000
SEARCH_FILE_BYTES = 2_000_000
MAX_MATCHES = 200
MAX_FILES = 500
LINE_CHARS = 300
SHELL_OUTPUT_CHARS = 20_000
SKIP_DIRS = {".git"}
#: Variables a shell command keeps; everything else, the API key included, is dropped.
SHELL_ENV_KEEP = ("PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR", "USER")
TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN")

SEVERITIES = ("info", "low", "medium", "high")

SYSTEM_PROMPT = """\
You are an agent running unattended in CI. Nobody can answer a question, so
decide for yourself and finish the task.

You work on the repository at {repo}. You can read, search and list files in
these folders, and nowhere else:

{roots}

Paths you pass to the file tools are relative to the repository, or absolute
inside one of the folders above. You can also run shell commands with
run_shell, in the repository folder; use it to run the scripts a skill ships
and commands a skill tells you to run.

Report only: never change, commit or push a file. Someone reads your report
and decides what to do.

## Skills

A skill is a folder of instructions for one kind of task. When a skill
matches your task, or part of it, read its SKILL.md with read_file before
you start and follow it. Paths a skill names are relative to its own folder.

{skills}

## Your report

Finish with a report: a short summary, a `checked` list and a `findings` list.

- `checked`: one entry per page or concept you compared, naming what you
  compared it against, with the evidence. Something that holds goes here,
  never in findings.
- `findings`: mismatches only. Each names the claim (path:line), the evidence
  that contradicts it (path:line strings), and a suggested fix. Give each a
  severity: high for something wrong that someone must fix, medium for
  something that is probably wrong or that you could not check, low for
  something minor.

Every citation is a path:line string, path relative to the repository, for a
line you actually read with read_file or got as a search_files hit. The report
is checked: a citation of a line you did not read or get from a search is sent
back.
"""

DEFAULT_PROMPT = """\
Audit this repository's knowledge: follow the audit skill.

There are no agents to dispatch: do the kmctl-auditor's work yourself, for
every batch in turn, following its instructions below. Your tools stand in for
the ones they name: read_file for Read, search_files for Grep and list_files
for Glob, and run_shell to run kmctl.

Put every concept you compared in `checked`. Turn each drifted verdict into a
high finding and each unsure verdict into a medium finding; a concept that
holds gets no finding. Use the concept's id as the finding's title.

=== The kmctl-auditor instructions ===

{auditor}
"""


class Checked(BaseModel):
    """One page or concept the agent compared."""

    subject: str = Field(description="The page or concept's path.")
    against: str = Field(description="What it was compared against, in a few words.")
    evidence: list[str] = Field(description="path:line strings you read.")


class Finding(BaseModel):
    """One mismatch the agent found."""

    title: str = Field(description="What the finding is about, in a few words.")
    severity: Literal["low", "medium", "high"]
    path: str = Field(description="The file the finding is about.")
    summary: str = Field(description="What is wrong, in a sentence or two.")
    claim: str = Field(description="path:line of the claim that does not hold.")
    contradicted_by: list[str] = Field(description="path:line strings that contradict it.")
    fix: str = Field(description="A suggested fix.")


class Report(BaseModel):
    """What the agent hands back."""

    summary: str
    checked: list[Checked]
    findings: list[Finding]


class Refused(Exception):
    """A request a tool will not serve; its text goes back to the model."""


class UsageError(Exception):
    """A bad setting; its text tells the caller what to change."""


@dataclass
class Workspace:
    """The folders the agent may read, and where its shell runs."""

    repo: Path
    roots: list[Path] = field(default_factory=list)
    shell_timeout: int = 120
    reads: dict = field(default_factory=dict)  # shown path -> list[(first, last)]
    hits: set = field(default_factory=set)  # (shown path, line)
    lengths: dict = field(default_factory=dict)  # shown path -> line count

    def resolve(self, raw: object) -> Path:
        """Resolve ``raw`` against the repository, following symlinks; refuse it outside every root."""
        text = str(raw or ".")
        path = Path(text)
        if not path.is_absolute():
            path = self.repo / path
        try:
            path = path.resolve()
        except (OSError, ValueError, RuntimeError) as err:
            raise Refused(f"cannot resolve {text!r}: {err}") from err
        if not any(self._inside(root, path) for root in self.roots):
            raise Refused(
                f"{text!r} is outside the folders you can read: "
                + ", ".join(str(r) for r in self.roots)
            )
        return path

    def _inside(self, root: Path, path: Path) -> bool:
        return path == root or path.is_relative_to(root)

    def show(self, path: Path) -> str:
        """Name ``path`` relative to the repository when it is inside it, else absolute."""
        return (
            os.path.relpath(path, self.repo)
            if self._inside(self.repo, path)
            else str(path)
        )

    def files(self, start: Path):
        """Yield ``(shown path, resolved file)`` under ``start`` in a stable order.

        Folder symlinks are not followed, and a file symlink that resolves
        outside every root is skipped.
        """
        if start.is_file():
            yield self.show(start), start
            return
        for folder, dirs, names in os.walk(start, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(names):
                walked = Path(folder) / name
                try:
                    real = walked.resolve()
                except (OSError, RuntimeError):
                    continue
                if any(self._inside(r, real) for r in self.roots) and real.is_file():
                    yield self.show(walked), real


def _number(raw: object, default: int, low: int, high: int) -> int:
    """Read an integer argument, falling back to ``default`` and clamping it."""
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


def make_tools(ws: Workspace) -> list:
    """Return the agent's tools, bound to ``ws``."""

    def guarded(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> str:
            try:
                return fn(*args, **kwargs)
            except Refused as err:
                return json.dumps({"error": str(err)})
            except OSError as err:
                return json.dumps({"error": f"could not read: {err.strerror or err}"})

        return wrapper

    @guarded
    def read_file(path: str, offset: int = 1, limit: int = READ_LINES) -> str:
        """Read a text file as 'LINE|text' lines.

        Long files are cut; the result then names the offset to read on from.

        Parameters
        ----------
        path
            The file: relative to the repository, or absolute inside a folder you can read.
        offset
            The first line to read, from 1.
        limit
            How many lines to read, at most 2000.
        """
        file = ws.resolve(path)
        if not file.is_file():
            raise Refused(f"{path!r} is not a file.")
        first = _number(offset, 1, 1, 10**9)
        most = _number(limit, READ_LINES, 1, READ_LINES)
        lines: list[str] = []
        used = number = 0
        cut_at = None
        with file.open("rb") as handle:
            while raw := handle.readline(READ_BYTES):
                number += 1
                if number < first:
                    continue
                if len(lines) == most or (lines and used + len(raw) > READ_BYTES):
                    cut_at = number
                    break
                used += len(raw)
                text = raw.decode("utf-8", "replace").rstrip("\n").rstrip("\r")
                lines.append(f"{number}|{text}")
        shown = ws.show(file)
        if lines:
            ws.reads.setdefault(shown, []).append((first, first + len(lines) - 1))
        if not lines:
            return f"{shown}: no lines from line {first} (the file has {number})."
        tail = (
            f"[cut: the file goes on; read again with offset={cut_at} for the rest]"
            if cut_at
            else "[end of file]"
        )
        return "\n".join(
            [f"{shown}, lines {first}-{first + len(lines) - 1}:", *lines, tail]
        )

    @guarded
    def search_files(pattern: str, path: str = ".", ignore_case: bool = False) -> str:
        """Find lines holding a piece of plain text, and return them as 'path:line: text'.

        The result says when it stopped at its match cap.

        Parameters
        ----------
        pattern
            The exact text to find; never read as a regex or an option.
        path
            A file or folder to search in; default the repository.
        ignore_case
            Match without regard to case.
        """
        if not pattern:
            raise Refused("give the text to search for in 'pattern'.")
        needle = pattern.casefold() if ignore_case else pattern
        matches: list[str] = []
        cut_files = 0
        for shown, real in ws.files(ws.resolve(path)):
            with real.open("rb") as handle:
                data = handle.read(SEARCH_FILE_BYTES + 1)
            if b"\0" in data[:8192]:
                continue
            if len(data) > SEARCH_FILE_BYTES:
                cut_files += 1
                data = data[:SEARCH_FILE_BYTES]
            for number, line in enumerate(
                data.decode("utf-8", "replace").split("\n"), 1
            ):
                line = line.rstrip("\r")
                if needle in (line.casefold() if ignore_case else line):
                    matches.append(f"{shown}:{number}: {line[:LINE_CHARS]}")
                    ws.hits.add((ws.show(real), number))
                    if len(matches) == MAX_MATCHES:
                        matches.append(
                            f"[stopped after {MAX_MATCHES} matches; search a narrower path or longer text.]"
                        )
                        return "\n".join(matches)
        if cut_files:
            matches.append(
                f"[{cut_files} file(s) larger than {SEARCH_FILE_BYTES} bytes were searched only up to that size.]"
            )
        return "\n".join(matches) if matches else f"no line holds {pattern!r}."

    @guarded
    def list_files(
        path: str = ".", contains: str = "", ignore_case: bool = False
    ) -> str:
        """List the files under a folder, one per line.

        Parameters
        ----------
        path
            The folder to list; default the repository.
        contains
            Only files whose path holds this text, such as '.py' or a file name.
        ignore_case
            Match `contains` without regard to case.
        """
        needle = contains.casefold() if ignore_case else contains
        found: list[str] = []
        for shown, _ in ws.files(ws.resolve(path)):
            if needle in (shown.casefold() if ignore_case else shown):
                if len(found) == MAX_FILES:
                    found.append(
                        f"[stopped after {MAX_FILES} files; list a narrower path or add 'contains'.]"
                    )
                    break
                found.append(shown)
        return "\n".join(found) if found else "no file matches."

    def run_shell(command: str) -> str:
        """Run a shell command in the repository folder and return its exit code and output.

        The command gets a clean environment: no API key and no GitHub token.

        Parameters
        ----------
        command
            The command, run with sh -c.
        """
        env = {k: os.environ[k] for k in SHELL_ENV_KEEP if k in os.environ}
        # Its own session, so the time limit stops everything the command started.
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=ws.repo,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=ws.shell_timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            return f"stopped: the command ran past {ws.shell_timeout}s."
        out = stdout + stderr
        if len(out) > SHELL_OUTPUT_CHARS:
            out = (
                out[:SHELL_OUTPUT_CHARS] + f"\n[cut at {SHELL_OUTPUT_CHARS} characters]"
            )
        return f"exit {proc.returncode}\n{out}"

    return [read_file, search_files, list_files, run_shell]


def find_skills(folders: list[Path]) -> list[tuple[str, str, Path]]:
    """Return ``(name, description, SKILL.md)`` for each skill under ``folders``.

    Raises
    ------
    UsageError
        If a folder is missing, or a SKILL.md has no name or description.
    """
    found = []
    for folder in folders:
        if not folder.is_dir():
            raise UsageError(f"--skills {folder}: no such folder.")
        for skill in sorted(folder.glob("*/SKILL.md")):
            text = skill.read_text()
            meta = None
            if match := re.match(r"---\n(.*?)\n---", text, re.DOTALL):
                try:
                    meta = yaml.safe_load(match.group(1))
                except yaml.YAMLError:
                    meta = None
            if (
                not isinstance(meta, dict)
                or not meta.get("name")
                or not meta.get("description")
            ):
                raise UsageError(
                    f"{skill}: its front matter needs a name and a description."
                )
            found.append((str(meta["name"]), str(meta["description"]), skill.resolve()))
    return found


def system_prompt(ws: Workspace, skills: list[tuple[str, str, Path]]) -> str:
    """Return the shipped system prompt, filled in for ``ws`` and ``skills``."""
    listed = "\n".join(f"- {name}: {desc}\n  ({path})" for name, desc, path in skills)
    return SYSTEM_PROMPT.format(
        repo=ws.repo,
        roots="\n".join(f"- {r}" for r in ws.roots),
        skills=listed or "(none)",
    )


def default_prompt() -> str:
    """Return the shipped user message: the kmctl knowledge audit."""
    auditor = AUDITOR.read_text() if AUDITOR.is_file() else "(not found)"
    return DEFAULT_PROMPT.format(auditor=auditor)


def build_model(name: str, base_url: str, key_env: str) -> Model | str:
    """Return the model to run.

    With ``base_url``, ``name`` is the model the endpoint serves, reached as an
    OpenAI-compatible API with the key from ``key_env``. Without it, ``name`` is
    PydanticAI's ``provider:model`` string and the provider reads its own key.

    Raises
    ------
    UsageError
        If ``key_env`` is not a variable name or the variable is empty.
    """
    if key_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key_env):
        raise UsageError(
            f"--api-key-env must be a variable name, such as AUDIT_API_KEY; got {key_env!r}."
        )
    if key_env and not os.environ.get(key_env):
        raise UsageError(
            f"{key_env} is empty; set it from the secret that holds the key, "
            "or leave out --api-key-env for an endpoint that takes none."
        )
    if not base_url:
        if key_env:
            raise UsageError(
                "--api-key-env needs --base-url; without it the provider reads "
                "its own variable, such as OPENAI_API_KEY."
            )
        return name
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    key = os.environ[key_env] if key_env else "none"
    return OpenAIChatModel(
        name, provider=OpenAIProvider(base_url=base_url, api_key=key)
    )


def refuse_tokens(repo: Path) -> None:
    """Refuse to run where a command could read a GitHub token.

    Raises
    ------
    UsageError
        If GH_TOKEN or GITHUB_TOKEN is set, or git config holds checkout's token.
    """
    for name in TOKEN_VARS:
        if os.environ.get(name):
            raise UsageError(
                f"refused: {name} is set, and the agent could read the token. "
                "Give it only to the publish job, which runs no agent."
            )
    held = subprocess.run(
        ["git", "config", "--get-regexp", r"^http\..*\.extraheader$"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if held.returncode == 0:
        raise UsageError(
            "refused: git config holds checkout's token (an extraheader), and the "
            "agent could read it. Check out with persist-credentials: false."
        )


def render(report: Report) -> str:
    """Return the report as Markdown: the summary, counts, then a table, most severe first."""

    def cell(text: object) -> str:
        return str(text).replace("|", "\\|").replace("\n", " ")

    counts = ", ".join(
        f"{sum(f.severity == s for f in report.findings)} {s}"
        for s in reversed(SEVERITIES)
    )
    lines = [
        "## Agent report",
        "",
        report.summary,
        "",
        f"{counts}.",
        "",
        "| Severity | Finding | Path | Summary | Claim | Contradicted by | Fix |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in sorted(report.findings, key=lambda f: -SEVERITIES.index(f.severity)):
        evidence = ", ".join(f"`{e}`" for e in f.contradicted_by)
        lines.append(
            f"| {f.severity} | {cell(f.title)} | `{cell(f.path)}` | {cell(f.summary)} | `{cell(f.claim)}` | {cell(evidence)} | {cell(f.fix)} |"
        )
    lines += ["", "### Checked", ""]
    for k in report.checked:
        lines.append(f"- `{k.subject}` against {k.against}: " + ", ".join(f"`{e}`" for e in k.evidence))
    return "\n".join(lines) + "\n"


async def run_agent(
    model: Model | str,
    instructions: str,
    prompt: str,
    ws: Workspace,
    timeout: float,
    max_requests: int,
):
    """Run the agent once and return PydanticAI's result."""
    agent = Agent(
        model,
        output_type=Report,
        instructions=instructions,
        tools=make_tools(ws),
        retries={"output": OUTPUT_RETRIES},
    )

    @agent.output_validator
    def check_citations(ctx: RunContext, report: Report) -> Report:
        """Send the report back when it cites a line the agent did not see."""
        cites = [c for f in report.findings for c in [f.claim, *f.contradicted_by]]
        cites += [c for k in report.checked for c in k.evidence]
        bad = []
        for cite in cites:
            kind = classify(ws, cite)
            if kind:
                bad.append((cite, kind))
        STATS["validator_calls"].append(
            {"total": len(cites), "bad": [{"cite": c, "kind": k} for c, k in bad]}
        )
        print(
            f"spike: validator call {len(STATS['validator_calls'])}: {len(bad)}/{len(cites)} rejected",
            file=sys.stderr,
            flush=True,
        )
        if bad:
            raise ModelRetry(
                "These citations name a line you neither read with read_file nor "
                "got as a search_files hit; read or search them, or drop them, then "
                "send the report again:\n"
                + "\n".join(f"- {c}: {k}" for c, k in bad)
            )
        return report

    return await asyncio.wait_for(
        agent.run(prompt, usage=USAGE, usage_limits=UsageLimits(request_limit=max_requests)),
        timeout,
    )


OUTPUT_RETRIES = 5
STATS: dict = {"validator_calls": []}
from pydantic_ai.usage import RunUsage
USAGE = RunUsage()
CITE = re.compile(r"^(.+?):(\d+)(?:-(\d+))?$")


def classify(ws: Workspace, cite: str) -> str:
    """Return why ``cite`` is bad, or an empty string when it is backed by a read or a search hit."""
    m = CITE.match(cite.strip().strip("`"))
    if not m:
        return "malformed (not path:line)"
    raw, lo = m.group(1), int(m.group(2))
    hi = int(m.group(3) or lo)
    try:
        real = ws.resolve(raw)
    except Refused:
        return "path outside the readable folders"
    shown = ws.show(real)
    if not real.is_file():
        return "no such file"
    if shown not in ws.lengths:
        with real.open("rb") as h:
            ws.lengths[shown] = sum(1 for _ in h)
    if hi > ws.lengths[shown]:
        return f"past the file end ({ws.lengths[shown]} lines)"
    ranges = ws.reads.get(shown, [])
    file_hits = {n for p, n in ws.hits if p == shown}
    ok = all(any(a <= n <= b for a, b in ranges) or n in file_hits for n in range(lo, hi + 1))
    if ok:
        return ""
    if not ranges and not file_hits:
        return "file never read or searched"
    if ranges:
        return "line outside the ranges read"
    return "line not a search hit (file only searched)"


def parse_duration(text: str) -> int:
    """Return seconds for ``90``, ``90s``, ``30m``, ``2h`` or ``1d``."""
    match = re.fullmatch(r"(\d+)([smhd]?)", text)
    if not match:
        raise UsageError(
            f"--timeout must be a number with s, m, h or d, such as 30m; got {text!r}."
        )
    unit = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
    return int(match.group(1)) * unit


def run(args: argparse.Namespace, model: Model | str | None = None) -> int:
    """Run the ``run`` command; ``model`` overrides ``--model`` (for tests)."""
    repo = Path(args.repo).resolve()
    contexts = [Path(c).resolve() for c in args.context]
    skill_dirs = [Path(s).resolve() for s in (args.skills or [DEFAULT_SKILLS])]
    for folder in contexts:
        if not folder.is_dir():
            raise UsageError(f"--context {folder}: no such folder.")
    if args.prompt is not None and args.prompt_file is not None:
        raise UsageError("give --prompt or --prompt-file, not both.")
    refuse_tokens(repo)
    timeout = parse_duration(args.timeout)
    ws = Workspace(repo, [repo, *contexts, *skill_dirs], args.shell_timeout)
    skills = find_skills(skill_dirs)
    instructions = (
        Path(args.system_prompt_file).read_text()
        if args.system_prompt_file
        else system_prompt(ws, skills)
    )
    if args.prompt is not None:
        prompt = args.prompt
    elif args.prompt_file is not None:
        prompt = Path(args.prompt_file).read_text()
    else:
        prompt = default_prompt()
    if model is None:
        model = build_model(args.model, args.base_url, args.api_key_env)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stats_file = out / "spike-stats.json"
    try:
        result = asyncio.run(
            run_agent(model, instructions, prompt, ws, timeout, args.max_requests)
        )
    except (TimeoutError, UnexpectedModelBehavior, UsageLimitExceeded) as err:
        STATS["finished"] = False
        STATS["error"] = f"{type(err).__name__}: {err}"
        STATS["requests"] = USAGE.requests
        STATS["retries"] = sum(1 for c in STATS["validator_calls"] if c["bad"])
        stats_file.write_text(json.dumps(STATS, indent=2))
        print(json.dumps(STATS, indent=2))
        return 1
    report = result.output
    STATS["finished"] = True
    STATS["requests"] = result.usage().requests
    STATS["retries"] = sum(1 for c in STATS["validator_calls"] if c["bad"])
    STATS["checked"] = len(report.checked)
    STATS["findings"] = len(report.findings)
    stats_file.write_text(json.dumps(STATS, indent=2))
    print(json.dumps(STATS, indent=2))
    markdown = render(report)
    (out / "report.json").write_text(report.model_dump_json(indent=2) + "\n")
    (out / "report.md").write_text(markdown)
    (out / "transcript.json").write_bytes(result.all_messages_json())
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as handle:
            handle.write(markdown)
    print(markdown, end="")
    print(
        f"agent: wrote report.json, report.md and transcript.json to {out}",
        file=sys.stderr,
    )
    return 0


#: Where GitHub looks for CODEOWNERS, in its order: the first one found is used.
CODEOWNERS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")


class GhFailed(Exception):
    """A gh call that failed; its text says which."""


def gh(*args: str) -> str:
    """Run ``gh`` and return its stdout.

    Raises
    ------
    GhFailed
        If gh is missing or exits nonzero.
    """
    try:
        proc = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError as err:
        raise GhFailed("gh is not on PATH.") from err
    if proc.returncode != 0:
        raise GhFailed(
            f"gh {' '.join(args[:2])} exited {proc.returncode}: {proc.stderr.strip()}"
        )
    return proc.stdout


def find_owners(repo: Path) -> list[str]:
    """Return the owners of the last ``*`` rule in the repository's CODEOWNERS, or none."""
    for rel in CODEOWNERS:
        path = repo / rel
        if path.is_file():
            owners: list[str] = []
            for line in path.read_text().splitlines():
                rule = line.split("#", 1)[0].split()
                if rule and rule[0] == "*":
                    owners = rule[1:]
            return [o for o in owners if o.startswith("@")]
    return []


def run_link() -> str:
    """Return the workflow run's URL, where its artifacts are, or empty outside Actions."""
    repo, run_id = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID")
    if not repo or not run_id:
        return ""
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    return f"{server}/{repo}/actions/runs/{run_id}"


def publish(args: argparse.Namespace) -> int:
    """Run the ``publish`` command: post the report to one issue, or close it."""
    try:
        report = Report.model_validate_json(Path(args.report).read_text())
    except (OSError, ValueError) as err:
        raise UsageError(f"cannot read the report {args.report}: {err}") from err
    repo = Path(args.repo)
    floor = SEVERITIES.index(args.min_severity)
    over = [f for f in report.findings if SEVERITIES.index(f.severity) >= floor]
    owners = (
        [m if m.startswith("@") else f"@{m}" for m in args.mention]
        if args.mention
        else find_owners(repo)
    )
    cc = " ".join(owners)
    link = run_link()
    try:
        listed = json.loads(
            gh(
                "issue",
                "list",
                "--state",
                "open",
                "--search",
                f'"{args.title}" in:title',
                "--json",
                "number,title",
            )
        )
        number = next(
            (str(i["number"]) for i in listed if i["title"] == args.title), ""
        )
        if not over:
            if number:
                gh(
                    "issue",
                    "comment",
                    number,
                    "--body",
                    f"The latest run found nothing at or above {args.min_severity}; closing."
                    + (f" Run: {link}" if link else ""),
                )
                gh("issue", "close", number)
                print(
                    f"agent: nothing at or above {args.min_severity}; closed issue #{number}.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"agent: nothing at or above {args.min_severity}; no issue was written.",
                    file=sys.stderr,
                )
            return 0
        body = render(report)
        if link:
            body += f"\nRun and its `agent-report` artifact: {link}\n"
        if cc:
            body = f"cc {cc}\n\n" + body
        counts = ", ".join(
            f"{sum(f.severity == s for f in over)} {s}"
            for s in reversed(SEVERITIES[floor:])
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
            handle.write(body)
        try:
            if number:
                gh("issue", "edit", number, "--body-file", handle.name)
                gh(
                    "issue",
                    "comment",
                    number,
                    "--body",
                    (f"{cc} " if cc else "")
                    + f"The latest run found {counts} at or above {args.min_severity}; the issue body has the report."
                    + (f" Run: {link}" if link else ""),
                )
                print(f"agent: updated issue #{number}.", file=sys.stderr)
            else:
                print(
                    gh(
                        "issue",
                        "create",
                        "--title",
                        args.title,
                        "--body-file",
                        handle.name,
                    ).strip()
                )
        finally:
            os.unlink(handle.name)
    except GhFailed as err:
        print(f"agent: {err}", file=sys.stderr)
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    top = argparse.ArgumentParser(
        prog="agent.py",
        description=(
            "A small agent for CI. `run` gives it a task and writes its report; "
            "`publish` posts that report to a GitHub issue. "
            "Exit codes: 0 the report was written, 1 the run failed, 2 a bad option."
        ),
    )
    sub = top.add_subparsers(dest="command", required=True)
    r = sub.add_parser(
        "run",
        help="Run the agent and write its report.",
        description=(
            "Run the agent on a repository and write report.json, report.md and "
            "transcript.json to --out; report.md also goes to stdout and to "
            "$GITHUB_STEP_SUMMARY when that is set. Refuses to start when "
            "GH_TOKEN or GITHUB_TOKEN is set or git config holds checkout's token."
        ),
    )
    r.add_argument(
        "--model",
        required=True,
        help=(
            "Without --base-url, PydanticAI's provider:model name, such as "
            "openai:gpt-5, anthropic:claude-sonnet-5-5, google-gla:gemini-3.8-flash "
            "or openrouter:qwen/qwen3-coder; the provider reads its own key "
            "variable (OPENAI_API_KEY and so on). With --base-url, the model name "
            "the endpoint serves. 'test' runs PydanticAI's offline test model."
        ),
    )
    r.add_argument(
        "--base-url",
        default="",
        help=(
            "An OpenAI-compatible endpoint's base URL, such as "
            "http://localhost:11434/v1 for Ollama. Default: empty, so --model's provider is used."
        ),
    )
    r.add_argument(
        "--api-key-env",
        default="",
        help=(
            "With --base-url, the name of the variable that holds the key, such "
            "as AUDIT_API_KEY. Default: empty, for an endpoint that takes no key."
        ),
    )
    r.add_argument(
        "--prompt",
        default=None,
        help="The task, as text. Default: the kmctl knowledge audit.",
    )
    r.add_argument(
        "--prompt-file",
        default=None,
        help="A file holding the task, instead of --prompt. Default: none.",
    )
    r.add_argument(
        "--system-prompt-file",
        default=None,
        help=(
            "A file that replaces the shipped system prompt, which lists the "
            "folders the agent can read and its skills. Default: the shipped one."
        ),
    )
    r.add_argument(
        "--context",
        action="append",
        default=[],
        metavar="DIR",
        help="A folder the agent can read as well as the repository, such as docs a workflow fetched. Repeatable. Default: none.",
    )
    r.add_argument(
        "--skills",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "A folder of skills (each a subfolder with a SKILL.md). Repeatable. "
            f"Default: kmctl's skills next to this script, {DEFAULT_SKILLS}."
        ),
    )
    r.add_argument(
        "--repo",
        default=".",
        help="The repository to work on. Default: the current folder.",
    )
    r.add_argument(
        "--out",
        default="agent-report",
        help="The folder to write the report to. Default: agent-report.",
    )
    r.add_argument(
        "--timeout",
        default="30m",
        help="How long the whole run may take: seconds, or with s, m, h or d. Default: 30m.",
    )
    r.add_argument(
        "--shell-timeout",
        type=int,
        default=120,
        help="How many seconds one shell command may take. Default: 120.",
    )
    r.add_argument(
        "--max-requests",
        type=int,
        default=200,
        help="How many model requests the run may make. Default: 200.",
    )
    p = sub.add_parser(
        "publish",
        help="Post a report to one GitHub issue.",
        description=(
            "Post report.json to the open issue titled --title with gh, when a "
            "finding is at or above --min-severity: create it, or replace its "
            "body and add a comment that mentions the owners. Below the "
            "threshold, close that issue with a comment. Needs gh and GH_TOKEN; "
            "run it in a job of its own, not the agent's. Exit codes: 0 done, "
            "1 gh failed, 2 a bad option or report."
        ),
    )
    p.add_argument("report", help="The report.json that run wrote.")
    p.add_argument(
        "--min-severity",
        choices=SEVERITIES,
        default="high",
        help="The lowest severity that opens or updates the issue. Default: high.",
    )
    p.add_argument(
        "--title",
        default="Knowledge audit",
        help="The issue's title. Default: Knowledge audit.",
    )
    p.add_argument(
        "--mention",
        action="append",
        default=[],
        metavar="USER",
        help=(
            "A user or team to mention, such as @alice or @org/team. Repeatable; "
            "replaces the owners of the last * rule in CODEOWNERS. Default: those owners."
        ),
    )
    p.add_argument(
        "--repo",
        default=".",
        help="The repository whose CODEOWNERS names the owners. Default: the current folder.",
    )
    return top


def main(argv: list[str] | None = None, model: Model | str | None = None) -> int:
    """Parse ``argv`` and run the command; return the exit code."""
    args = parser().parse_args(argv)
    try:
        if args.command == "publish":
            return publish(args)
        return run(args, model)
    except UsageError as err:
        print(f"agent: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
