# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pydantic-ai-slim[openai]==2.57.0",
#   "pyyaml>=6.0.3",
# ]
# ///
"""Reread, on a pull request, the pages whose sources it changed (ADR 0060).

Run it with ``uv run action/agent.py run --help``. It needs nothing from kmctl.
``run`` lists every page under ``.okf/`` and ``docs/`` whose ``sources`` name a
file changed since ``--base``, hands that list and the shipped prompt
(``action/prompt.md``) to a model, and writes the typed report to ``--out`` as
``report.json``, ``report.md`` and ``transcript.json``. With nothing in scope
it writes an empty report without calling the model. The agent can only read,
search and list files in the repository; it has no shell.

``publish`` posts that report as one comment on a pull request, and replaces
it on the next run, with ``gh``. Run it in a job of its own, which gets the
report as an artifact and nothing else from the agent's job, so nothing the
agent changed runs with the token.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import json
import os
import re
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
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.models import Model
from pydantic_ai.usage import UsageLimits

HERE = Path(__file__).resolve().parent
#: The task the agent gets, before the list of pages in scope.
PROMPT = HERE / "prompt.md"
#: Marks publish's pull request comment, so the next run finds and replaces it.
COMMENT_MARK = "<!-- kmctl-audit: {title} -->"

READ_BYTES = 100_000
READ_LINES = 2000
SEARCH_FILE_BYTES = 2_000_000
MAX_MATCHES = 200
MAX_FILES = 500
LINE_CHARS = 300
#: How many times a report goes back to the agent for unchecked citations.
OUTPUT_RETRIES = 5
SKIP_DIRS = {".git"}
TOKEN_VARS = ("GH_TOKEN", "GITHUB_TOKEN")
#: Statuses whose page claims nothing about the code any more.
RETIRED = {"deprecated", "superseded"}

SEVERITIES = ("info", "low", "medium", "high")

SYSTEM_PROMPT = """\
You are an agent running unattended in CI. Nobody can answer a question, so
decide for yourself and finish the task.

You work on the repository at {repo}. You can read, search and list files in
it, and nowhere else. Paths you pass to the file tools are relative to the
repository. You have no shell.

Report only: never change, commit or push a file. Someone reads your report
and decides what to do.

## Your report

Finish with a report: a short summary, a checked list and a findings list.

- checked: one entry per page you compared, naming what you compared it
  against, with evidence. Something that holds goes here, never in findings.
- findings: mismatches only. Each names the claim that does not hold
  (path:line), the lines that contradict it (path:line), and a suggested
  fix. Rate it by what a reader of the page would get wrong: high for a
  claim the code contradicts that would lead a reader to act wrongly, such
  as a name, default, path, option or step the code does not have; medium
  for a claim that is probably wrong, or that you could not check; low for
  a claim that is wrong but would still leave a reader acting correctly,
  such as a wrong reason for a right result; info for a note that needs no
  fix.

Cite a line as path:line, or a range as path:first-last, with the path
relative to the repository. The report is checked: a citation of a line you
did not read with read_file or get as a search_files hit, or of a line past
the file's end, is sent back.
"""


class Checked(BaseModel):
    """One thing the agent compared."""

    subject: str = Field(description="The page, concept or file compared.")
    against: str = Field(description="What it was compared against, in a few words.")
    evidence: list[str] = Field(description="path:line strings you read.")


class Finding(BaseModel):
    """One mismatch the agent found."""

    title: str = Field(description="What the finding is about, in a few words.")
    severity: Literal["info", "low", "medium", "high"]
    path: str = Field(description="The file the finding is about.")
    summary: str = Field(description="What is wrong, in a sentence or two.")
    claim: str = Field(description="path:line of the claim that does not hold.")
    contradicted_by: list[str] = Field(
        description="path:line strings that contradict the claim."
    )
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
    """The folders the agent may read, and what it has read in them."""

    repo: Path
    roots: list[Path] = field(default_factory=list)
    #: Line ranges read_file returned, by resolved file.
    read: dict[Path, list[tuple[int, int]]] = field(default_factory=dict)
    #: Lines search_files returned, by resolved file.
    hits: dict[Path, set[int]] = field(default_factory=dict)
    #: The citations the last report was sent back for.
    unchecked: list[str] = field(default_factory=list)

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
    """Return the agent's tools, bound to ``ws``: read_file, search_files and list_files."""

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
        if not lines:
            return f"{shown}: no lines from line {first} (the file has {number})."
        ws.read.setdefault(file, []).append((first, first + len(lines) - 1))
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
                    ws.hits.setdefault(real, set()).add(number)
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

    return [read_file, search_files, list_files]


def git_lines(cwd: Path, *args: str) -> list[str]:
    """Run git in ``cwd`` and return its output lines.

    Raises
    ------
    UsageError
        If git exits nonzero.
    """
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise UsageError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.splitlines()


def source_matches(source: str, changed: list[str]) -> list[str]:
    """Return the changed files ``source`` covers: a file by its path, a folder as a prefix."""
    s = source.lstrip("/")
    if s.endswith("/"):
        return [p for p in changed if p.startswith(s)]
    return [p for p in changed if p == s or p.startswith(s + "/")]


@dataclass(frozen=True)
class Page:
    """A page in scope: its path, its status and the changed files its sources cover.

    Attributes
    ----------
    path : str
        The page, relative to the repository.
    status : str
        The page's ``status`` (``stable``, ``draft`` and so on), or
        ``docs page`` for a page under ``docs/``, which has none.
    files : list[str]
        The changed files its ``sources`` name, a folder source as a prefix.
    """

    path: str
    status: str
    files: list[str]


def front_matter(path: Path) -> dict:
    """Return the YAML front matter of the markdown file ``path``, or an empty dict."""
    match = re.match(r"---\n(.*?)\n---", path.read_text(errors="replace"), re.DOTALL)
    try:
        meta = yaml.safe_load(match.group(1)) if match else None
    except yaml.YAMLError:
        meta = None
    return meta if isinstance(meta, dict) else {}


def candidate_pages(repo: Path) -> list[Path]:
    """Return every page that can name sources: markdown under ``.okf/`` and ``docs/``.

    Handoffs, the log and the generated ``index.md`` pages are left out.
    """
    found = []
    for folder in (".okf", "docs"):
        for path in sorted((repo / folder).rglob("*.md")):
            rel = path.relative_to(repo).as_posix()
            if rel.startswith(".okf/handoffs/") or rel == ".okf/log.md":
                continue
            if path.name == "index.md":
                continue
            found.append(path)
    return found


def changed_pages(repo: Path, base: str) -> list[Page]:
    """Return each page whose ``sources`` name a file changed since ``base``.

    The change is ``git diff BASE...HEAD`` in ``repo``, with paths relative to
    ``repo``, where pages write their ``sources``. A renamed or moved file
    counts under its old path and its new one. URL sources are skipped, and
    so is a page whose status is deprecated or superseded.

    Raises
    ------
    UsageError
        If git cannot compare ``base`` with ``HEAD``.
    """
    # --no-renames lists a renamed file's old path too, so a page that still
    # names the old path comes into scope.
    changed = git_lines(
        repo, "diff", "--name-only", "--no-renames", "--relative", f"{base}...HEAD"
    )
    found = []
    for path in candidate_pages(repo):
        meta = front_matter(path)
        status = str(meta.get("status") or "")
        if status in RETIRED:
            continue
        files: list[str] = []
        for entry in meta.get("sources") or []:
            resource = str(entry.get("resource", "")) if isinstance(entry, dict) else ""
            if resource and "://" not in resource:
                files += [
                    f for f in source_matches(resource, changed) if f not in files
                ]
        if files:
            rel = path.relative_to(repo).as_posix()
            found.append(
                Page(
                    rel,
                    status or ("docs page" if rel.startswith("docs/") else ""),
                    files,
                )
            )
    return found


def scope_text(pages: list[Page], base: str) -> str:
    """Return the task's list of the pages in scope, compared with ``base``."""
    lines = [f"\n## Pages in scope\n\nThe change compared with {base}:\n"]
    for page in pages:
        lines.append(f"- {page.path} ({page.status}): " + ", ".join(page.files))
    return "\n".join(lines) + "\n"


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
    """Refuse to run where the agent could read a GitHub token.

    The agent has no shell, so it cannot read the environment, but read_file
    reaches ``.git/config``, where checkout leaves its token unless told not to.

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
    """Return the report as Markdown: the summary, counts, a table of findings
    (most severe first), then the checked list."""

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
        "| Severity | Finding | Summary | Claim | Contradicted by | Fix |",
        "|---|---|---|---|---|---|",
    ]
    for f in sorted(report.findings, key=lambda f: -SEVERITIES.index(f.severity)):
        against = ", ".join(f"`{cell(c)}`" for c in f.contradicted_by)
        lines.append(
            f"| {f.severity} | {cell(f.title)} | {cell(f.summary)} | `{cell(f.claim)}` | {against} | {cell(f.fix)} |"
        )
    lines += ["", f"### Checked ({len(report.checked)})", ""]
    for c in report.checked:
        evidence = ", ".join(f"`{e}`" for e in c.evidence)
        lines.append(f"- `{c.subject}` against {c.against}: {evidence}")
    return "\n".join(lines) + "\n"


CITATION = re.compile(r"(.+):(\d+)(?:-(\d+))?")


def bad_citations(ws: Workspace, report: Report) -> list[str]:
    """Return each citation in ``report`` the agent did not see, with why."""
    cited = [c for f in report.findings for c in (f.claim, *f.contradicted_by)]
    cited += [e for c in report.checked for e in c.evidence]
    bad = []
    for cite in cited:
        match = CITATION.fullmatch(cite.strip().strip("`"))
        if not match:
            bad.append(f"{cite}: not path:line or path:first-last")
            continue
        first = int(match.group(2))
        last = int(match.group(3) or first)
        if not 1 <= first <= last:
            bad.append(f"{cite}: lines count from 1, and a range runs first-last")
            continue
        try:
            file = ws.resolve(match.group(1))
        except Refused as err:
            bad.append(f"{cite}: {err}")
            continue
        if not file.is_file():
            bad.append(f"{cite}: no such file")
            continue
        with file.open("rb") as handle:
            length = sum(1 for _ in handle)
        if last > length:
            bad.append(f"{cite}: past the end of the file ({length} lines)")
            continue
        ranges = ws.read.get(file, [])
        hits = ws.hits.get(file, set())
        unseen = [
            n
            for n in range(first, last + 1)
            if n not in hits and not any(a <= n <= b for a, b in ranges)
        ]
        if unseen:
            bad.append(f"{cite}: line {unseen[0]} was neither read nor a search hit")
    return bad


async def run_agent(
    model: Model | str,
    instructions: str,
    prompt: str,
    ws: Workspace,
    timeout: float,
    max_requests: int,
):
    """Run the agent once and return PydanticAI's result.

    The report goes back to the agent, up to ``OUTPUT_RETRIES`` times, while
    it cites a line the agent did not see.
    """
    agent = Agent(
        model,
        output_type=Report,
        instructions=instructions,
        tools=make_tools(ws),
        retries={"output": OUTPUT_RETRIES},
    )

    @agent.output_validator
    def check_citations(report: Report) -> Report:
        ws.unchecked = bad_citations(ws, report)
        if bad := ws.unchecked:
            raise ModelRetry(
                "Cite only lines you read with read_file or got as a search_files "
                "hit. Read or search these, or drop them, then send the report "
                "again:\n" + "\n".join(f"- {b}" for b in bad)
            )
        return report

    return await asyncio.wait_for(
        agent.run(prompt, usage_limits=UsageLimits(request_limit=max_requests)),
        timeout,
    )


def parse_duration(text: str) -> int:
    """Return seconds for ``90``, ``90s``, ``30m``, ``2h`` or ``1d``."""
    match = re.fullmatch(r"(\d+)([smhd]?)", text)
    if not match:
        raise UsageError(
            f"--timeout must be a number with s, m, h or d, such as 30m; got {text!r}."
        )
    unit = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
    return int(match.group(1)) * unit


def write_report(out: Path, report: Report, transcript: bytes) -> None:
    """Write ``report`` to ``out`` as JSON and Markdown, and the transcript; echo the Markdown.

    The Markdown also goes to ``$GITHUB_STEP_SUMMARY`` when that is set.
    """
    out.mkdir(parents=True, exist_ok=True)
    markdown = render(report)
    (out / "report.json").write_text(report.model_dump_json(indent=2) + "\n")
    (out / "report.md").write_text(markdown)
    (out / "transcript.json").write_bytes(transcript)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a") as handle:
            handle.write(markdown)
    print(markdown, end="")
    print(
        f"agent: wrote report.json, report.md and transcript.json to {out}",
        file=sys.stderr,
    )


def run(args: argparse.Namespace, model: Model | str | None = None) -> int:
    """Run the ``run`` command; ``model`` overrides ``--model`` (for tests)."""
    repo = Path(args.repo).resolve()
    refuse_tokens(repo)
    timeout = parse_duration(args.timeout)
    pages = changed_pages(repo, args.base)
    if not pages:
        empty = Report(
            summary=(
                f"No page under .okf/ or docs/ names a file this change touched "
                f"(compared with {args.base}) in its sources, so nothing was reread."
            ),
            checked=[],
            findings=[],
        )
        write_report(Path(args.out), empty, b"[]")
        return 0
    if model is None:
        model = build_model(args.model, args.base_url, args.api_key_env)
    ws = Workspace(repo, [repo])
    prompt = PROMPT.read_text() + scope_text(pages, args.base)
    try:
        result = asyncio.run(
            run_agent(
                model,
                SYSTEM_PROMPT.format(repo=repo),
                prompt,
                ws,
                timeout,
                args.max_requests,
            )
        )
    except TimeoutError:
        print(f"agent: stopped after the time limit ({args.timeout}).", file=sys.stderr)
        return 1
    except UnexpectedModelBehavior as err:
        if ws.unchecked:
            print(
                f"agent: stopped; after {OUTPUT_RETRIES} retries the report still cites "
                "lines the agent did not see, so its citations could not be checked:\n"
                + "\n".join(f"- {b}" for b in ws.unchecked),
                file=sys.stderr,
            )
        else:
            print(f"agent: stopped; the model failed: {err}", file=sys.stderr)
        return 1
    write_report(Path(args.out), result.output, result.all_messages_json())
    return 0


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


def run_link() -> str:
    """Return the workflow run's URL, where its artifacts are, or empty outside Actions."""
    repo, run_id = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID")
    if not repo or not run_id:
        return ""
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    return f"{server}/{repo}/actions/runs/{run_id}"


def publish_comment(args: argparse.Namespace, report: Report, over: list) -> int:
    """Post the report as one comment on pull request ``args.pr``, replacing the last one.

    With nothing at or above the threshold and no earlier comment, it posts
    nothing.
    """
    mark = COMMENT_MARK.format(title=args.title)
    link = run_link()
    try:
        comments = json.loads(
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/issues/{args.pr}/comments",
                "--paginate",
                "--slurp",
            )
            or "[]"
        )
        flat = [
            c for page in comments for c in (page if isinstance(page, list) else [page])
        ]
        # Only a body that starts with the mark is ours; a quote of it starts with "> ".
        earlier = next(
            (c for c in flat if str(c.get("body", "")).startswith(mark)), None
        )
        if not over and earlier is None:
            print(
                f"agent: nothing at or above {args.min_severity}; no comment was written.",
                file=sys.stderr,
            )
            return 0
        body = f"{mark}\n## {args.title}\n\n"
        if over:
            body += render(report)
        else:
            body += f"The latest run found nothing at or above {args.min_severity}.\n"
        if link:
            body += f"\nRun and its report artifact: {link}\n"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as handle:
            handle.write(body)
        try:
            if earlier is not None:
                gh(
                    "api",
                    "-X",
                    "PATCH",
                    f"repos/{{owner}}/{{repo}}/issues/comments/{earlier['id']}",
                    "-F",
                    f"body=@{handle.name}",
                )
                print(
                    f"agent: replaced the audit comment on pull request #{args.pr}.",
                    file=sys.stderr,
                )
            else:
                gh("pr", "comment", str(args.pr), "--body-file", handle.name)
                print(f"agent: commented on pull request #{args.pr}.", file=sys.stderr)
        finally:
            os.unlink(handle.name)
    except GhFailed as err:
        print(f"agent: {err}", file=sys.stderr)
        return 1
    return 0


def publish(args: argparse.Namespace) -> int:
    """Run the ``publish`` command: post the report as one pull request comment.

    A missing report, from an audit that was skipped or failed, posts nothing
    and exits 0.
    """
    if not Path(args.report).exists():
        print(
            f"agent: no report at {args.report}, so nothing to post; the audit "
            "was skipped or failed, and its own job shows why.",
            file=sys.stderr,
        )
        return 0
    try:
        report = Report.model_validate_json(Path(args.report).read_text())
    except (OSError, ValueError) as err:
        raise UsageError(f"cannot read the report {args.report}: {err}") from err
    floor = SEVERITIES.index(args.min_severity)
    over = [f for f in report.findings if SEVERITIES.index(f.severity) >= floor]
    return publish_comment(args, report, over)


def parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    top = argparse.ArgumentParser(
        prog="agent.py",
        description=(
            "Reread, on a pull request, the .okf/ and docs/ pages whose sources it "
            "changed. `run` writes the report; `publish` posts it as one pull "
            "request comment. Exit codes: 0 the report was written, 1 the run "
            "failed, 2 a bad option."
        ),
    )
    sub = top.add_subparsers(dest="command", required=True)
    r = sub.add_parser(
        "run",
        help="Reread the pages a change touched and write the report.",
        description=(
            "List every page under .okf/ and docs/ whose sources name a file "
            "changed since --base, have the model reread each against the change, "
            "and write report.json, report.md and transcript.json to --out; "
            "report.md also goes to stdout and to $GITHUB_STEP_SUMMARY when that "
            "is set. With nothing in scope, write an empty report without calling "
            "the model. Refuses to start when GH_TOKEN or GITHUB_TOKEN is set or "
            "git config holds checkout's token."
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
        "--base",
        required=True,
        metavar="REF",
        help=(
            "The branch the change is compared with, from the commit where the "
            "two split, such as origin/main. Needs the branch's history."
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
        "--max-requests",
        type=int,
        default=200,
        help="How many model requests the run may make. Default: 200.",
    )
    p = sub.add_parser(
        "publish",
        help="Post a report as one pull request comment.",
        description=(
            "Post report.json as one comment on pull request --pr with gh, marked "
            "with --title, and replace that comment on the next run. With no "
            "finding at or above --min-severity and no earlier comment, post "
            "nothing. With no report.json, post nothing and exit 0. Needs gh, "
            "GH_TOKEN and pull-requests: write; run it in a job of its own, not "
            "the agent's. Exit codes: 0 done, 1 gh failed, 2 a bad option or an "
            "unreadable report."
        ),
    )
    p.add_argument("report", help="The report.json that run wrote.")
    p.add_argument(
        "--pr",
        type=int,
        required=True,
        metavar="N",
        help="The pull request to comment on.",
    )
    p.add_argument(
        "--min-severity",
        choices=SEVERITIES,
        default="low",
        help="The lowest severity that posts or updates the comment. Default: low.",
    )
    p.add_argument(
        "--title",
        default="Knowledge audit",
        help="The comment's heading, which also marks it for replacing. Default: Knowledge audit.",
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
