"""An agent that turns a batch of claims into checks: steps that later run against the repository with no model.

The agent reads the repository through a few tools, tries each check before it hands it in, and submits one check
or one reason per claim. Two things keep its cost bounded:

- Old tool output can be trimmed (``Budget.trim``): only the newest tool results are sent in full; older ones
  become a one-line note of what was asked, which the agent can ask again. Off, the history is sent as it grew,
  which a provider's prompt cache can serve.
- Each batch has its own turn and token budget. Near the end the agent is told to submit; at the end it gets one
  last call that can only submit, and claims still open after it are reported unfinished, so one hard batch cannot
  spend the run.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel, Field, ValidationError, field_validator

from audit_cli.checks.steps import Repository, Step, StepResult, find_code, outline, run_check
from audit_cli.logs import get_logger

log = get_logger("checks.writer")

PROMPT = """
You turn claims about a repository into checks. A check is a list of steps that later runs against the repository
with no model, on every audit, so a good check saves a model call forever. A check holds when every step holds.

Steps:
- file: a tracked path or glob exists (exists: true) or does not (exists: false).
- grep: a Python regex matches some line (present: true) or none (present: false) in a glob of files.
- code: code of a given shape appears in a glob of source files (Python, shell, JavaScript, TypeScript, Rust, Java,
  Ruby). Write the code as it would appear, with $NAME for any one expression and $$$NAME for any run of arguments
  or statements: subprocess.run($$$A, timeout=120), if not $X: $$$B, sys.exit(1). It never matches comments or
  strings and ignores line breaks. The pattern must be a whole expression or statement: write
  f($$$A, timeout=120), not timeout=120. It tests presence only: test that code is absent with grep. In shell,
  $NAME is that shell variable, as written, and a command with more arguments after the pattern still matches: use
  grep for an exact command line.
- query: a JMESPath query over YAML, TOML or JSON files; expect equals, every, contains, not_empty or empty.
- definition: a Python function, class or assigned name is defined (or not) in a glob of Python files.
- imports: a Python file imports a top-level module (or not).
- help: a command of the repository's own CLI prints --help text matching a regex (or not).

Rules:
- A check must fail if the claim were false. Test what the claim says, not a word from it: "the default
  --min-severity is high" needs the default, not just the flag.
- To test what code does, prefer code over grep: a call and its argument, a condition and its exit. Use grep for
  text in files no code step reads.
- Markdown files and .okf/ are never read: they restate the claims.
- Prefer one or two narrow steps over many loose ones. Pin a regex to the code that does the thing (a condition and
  its exit, an argument and its default), not to a comment or docstring.
- strength "exact": the steps decide the claim. "proxy": they show the code the claim is about exists in the shape
  the claim needs, but behaviour still has to be read (say what in why).
- When no step can test a claim (behaviour across several files, what a runner or person does, history, intent),
  give a reason instead of a check. A proxy that tests nothing the claim says is worse than a reason.
- Submit each claim as soon as its check or reason is ready; do not hold them back for the end.
- Run try_check on each check before you submit it. A check that does not hold may mean the claim is wrong: then
  look once more, and submit the check that tests the claim; do not bend it until it holds.
- Scope each step to the files the claim is about: the audit's workflow, not every workflow. To test one job or
  step of a YAML file, use query (jobs.audit.steps[].env), not grep over the whole file.
- In JMESPath, quote a key with a hyphen: steps[].with."persist-credentials". Guard a function against a missing
  key, since starts_with(uses, ...) fails on a step with no uses: [?uses && starts_with(uses, 'actions/checkout')].
  YAML reads a workflow's on: key as
  true, so query triggers with grep instead.
- Read only what you need: search before you read, and read line ranges, not whole files.
- A check that still fails after you looked again means the claim is wrong: start its why with "drift:".
""".strip()
PROMPT_HASH = hashlib.sha256(PROMPT.encode()).hexdigest()[:8]
KEEP_CHARS = 24_000  # about 6k tokens of the newest tool output is sent in full
READ_LINES = 120
REMIND_EVERY = 5  # every this many turns the agent is told which claims are open
MAX_CHARS = 6000


class ListFiles(BaseModel):
    """List the readable tracked files matching a glob (markdown and .okf/ are left out)."""

    glob: str = Field(description="Like action/*.py, .github/workflows/*.yml or src/**.")


class ReadFile(BaseModel):
    """Read a line range of one file."""

    path: str
    start: int = Field(default=1, description="First line, from 1.")
    end: int = Field(default=0, description=f"Last line; 0 reads {READ_LINES} lines from start.")


class Search(BaseModel):
    """Search a glob of files for a Python regex; returns path:line: text for the first matches."""

    pattern: str
    paths: str = Field(default="**", description="A glob of files.")


class TryCheck(BaseModel):
    """Run a check's steps now and see whether each holds, and what it saw."""

    steps: list[Step]


class ClaimCheck(BaseModel):
    """The check for one claim."""

    claim: str = Field(description="The claim's label, like c3.")
    steps: list[Step] = Field(min_length=1, description="At least one step; with none, give a NoCheck instead.")
    strength: Literal["exact", "proxy"]
    why: str = Field(
        description="One sentence: why these steps hold exactly when the claim does, or what a proxy misses."
    )


class NoCheck(BaseModel):
    """A claim no step can test."""

    claim: str = Field(description="The claim's label, like c3.")
    reason: str = Field(description="One sentence: why no step can test it.")


class Submit(BaseModel):
    """Hand in a check or a reason for one or more claims, as soon as each is ready; the batch ends when all are in."""

    checks: list[ClaimCheck] = Field(default_factory=list)
    no_checks: list[NoCheck] = Field(default_factory=list)

    @field_validator("checks", "no_checks", mode="before")
    @classmethod
    def _from_text(cls, value: Any) -> Any:
        """Read a list sent as JSON text, as DeepSeek sometimes sends it."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


class CodeSearch(BaseModel):
    """Find code of a given shape (an ast-grep pattern, written as for a code step) in a glob of source files."""

    pattern: str = Field(description="Code with $NAME and $$$NAME wildcards, like subprocess.run($$$A, timeout=$T).")
    paths: str = Field(default="**", description="A glob of source files.")


class Outline(BaseModel):
    """List a file's functions and classes, or a YAML file's keys, with their line ranges."""

    path: str


TOOLS: dict[str, type[BaseModel]] = {t.__name__: t for t in (ListFiles, ReadFile, Search, TryCheck, Submit)}
CODE_TOOLS: dict[str, type[BaseModel]] = {t.__name__: t for t in (CodeSearch, Outline)}
CODE_TOOLS_NOTE = """
- Use Outline to see a file's parts and their lines before you read it, and CodeSearch to find the pattern that
  matches before you put it in a code step.
""".rstrip()
HINTS = """
Syntax that often fails:
- A code pattern: an elif, else, except or finally clause is not a pattern on its own. Match the whole if or try,
  with $$$ for the parts you do not care about, or grep that one line. A keyword argument needs its call:
  f($$$A, timeout=120), not timeout=120.
- JMESPath: jobs.*.steps[] flattens every job's steps; filter after it: jobs.*.steps[] | [?env.GH_TOKEN].name.
  Guard a function against a missing key: [?uses && starts_with(uses, 'x')].
- paths is one glob string, never a list.
""".rstrip()


@dataclass
class Budget:
    """What one batch may spend.

    Attributes
    ----------
    max_turns : int
        Model calls for the batch; two before the end the agent is told to submit, and the last call can only
        submit.
    max_tokens : int
        Input plus output tokens for the batch; past 80% the agent is told to submit, and once the next call, guessed
        as the last call's size plus its growth, would pass it, the next call is the last, submit-only one. The guess
        can fall short (one reply's reads can be far bigger than the last), so a batch can pass the budget by up to
        one normal call plus the last call, which is tried twice when its first answer cannot be read.
    trim : bool
        Send older tool results as short notes. Off, the history is sent as it grew, so each call starts with the
        last call's whole input, which a provider's prompt cache can serve.
    """

    max_turns: int = 20
    max_tokens: int = 250_000
    trim: bool = True


@dataclass
class ClaimInput:
    """One claim as shown to the agent, with where its named things were found and lines already found for it.

    The lines go in the first message, after the claims, so the agent need not search for them.
    """

    label: str
    claim_id: str
    text: str
    located: list[str] = field(default_factory=list)
    lines: str = ""


@dataclass
class WrittenCheck:
    """A submitted check and whether it holds now."""

    claim_id: str
    check: ClaimCheck
    holds: bool
    results: list[StepResult]


@dataclass
class BatchResult:
    """What one batch produced and spent.

    Attributes
    ----------
    checks : list[WrittenCheck]
        Submitted checks, each run once.
    no_checks : dict[str, str]
        Claim id to the reason no step can test it.
    unfinished : list[str]
        Claim ids the batch did not submit before its budget ran out.
    stopped : str | None
        Why the batch stopped early, if it did.
    calls : list[str]
        Each tool call, with the start of its arguments and of its answer, to see where a batch spent its turns.
    tokens_cached : int
        Input tokens the provider served from its prompt cache, as it reports them.
    chars_sent, chars_untrimmed : int
        Characters of history sent over the batch, and what sending it untrimmed would have been.
    """

    checks: list[WrittenCheck] = field(default_factory=list)
    no_checks: dict[str, str] = field(default_factory=dict)
    unfinished: list[str] = field(default_factory=list)
    turns: int = 0
    tokens_in: int = 0
    tokens_cached: int = 0
    tokens_out: int = 0
    trimmed: int = 0
    stopped: str | None = None
    calls: list[str] = field(default_factory=list)
    chars_sent: int = 0
    chars_untrimmed: int = 0


def _message(claims: list[ClaimInput]) -> str:
    """Build the first user message: the claims with where their named things were found, then lines found for them.

    A block of lines two claims share is shown once.
    """
    lines = ["Write a check, or give a reason, for each claim:", ""]
    for claim in claims:
        lines.append(f"{claim.label}: {claim.text}")
        if claim.located:
            lines.append(f"    found: {', '.join(claim.located[:6])}")
    shown = list(dict.fromkeys(c.lines for c in claims if c.lines))
    if shown:
        lines += ["", "Lines already found in the repository; read more only if these are not enough:", *shown]
    return "\n".join(lines)


def _tool(repo: Repository, name: str, args: dict[str, Any]) -> str:
    """Run one reading tool and return its text, cut to a bounded size."""
    parsed = (TOOLS | CODE_TOOLS)[name].model_validate(args)
    if isinstance(parsed, CodeSearch):
        hits = find_code(repo, parsed.pattern, repo.match(parsed.paths))
        text = "\n".join(hits[:40]) + (f"\n... {len(hits) - 40} more" if len(hits) > 40 else "") or "no match"
    elif isinstance(parsed, Outline):
        if parsed.path not in repo.files:
            return f"{parsed.path} is not a readable tracked file"
        text = "\n".join(outline(repo, parsed.path)) or "nothing to outline"
    elif isinstance(parsed, ListFiles):
        found = repo.match(parsed.glob)
        text = "\n".join(found[:200]) + (f"\n... {len(found) - 200} more" if len(found) > 200 else "")
    elif isinstance(parsed, ReadFile):
        if parsed.path not in repo.files:
            return f"{parsed.path} is not a readable tracked file"
        lines = repo.text(parsed.path).splitlines()
        end = parsed.end or parsed.start + READ_LINES - 1
        text = "\n".join(f"{n}: {lines[n - 1]}" for n in range(max(parsed.start, 1), min(end, len(lines)) + 1))
        text += f"\n({len(lines)} lines in all)"
    elif isinstance(parsed, Search):
        pattern = re.compile(parsed.pattern)
        hits = [
            f"{f}:{n}: {line.strip()[:160]}"
            for f in repo.match(parsed.paths)
            for n, line in enumerate(repo.text(f).splitlines(), 1)
            if pattern.search(line)
        ]
        text = "\n".join(hits[:40]) + (f"\n... {len(hits) - 40} more" if len(hits) > 40 else "") or "no match"
    else:
        assert isinstance(parsed, TryCheck)
        holds, results = run_check(repo, parsed.steps)
        text = json.dumps({"holds": holds, "steps": [r.model_dump() for r in results]})
    return text[:MAX_CHARS]


def _trimmed(history: list[BaseMessage]) -> tuple[list[BaseMessage], int]:
    """Return the history to send: the newest tool results in full, older ones as a note of what was asked.

    Newest first, results are kept until they reach ``KEEP_CHARS`` (the newest always is); an older copy of a call asked again is always
    trimmed, since the newer copy holds the same text. A result shorter than its note is sent as it is.
    """
    kept_chars = 0
    seen: set[tuple[str | None, object]] = set()
    old: set[int] = set()
    for i in reversed([i for i, m in enumerate(history) if isinstance(m, ToolMessage)]):
        message = history[i]
        key = (message.name, message.additional_kwargs.get("asked"))
        if key in seen or kept_chars and kept_chars + len(str(message.content)) > KEEP_CHARS:
            old.add(i)
        else:
            kept_chars += len(str(message.content))
        seen.add(key)
    sent: list[BaseMessage] = []
    for i, message in enumerate(history):
        note = f"[trimmed: {message.name}({message.additional_kwargs.get('asked', '')}); call it again if needed]"
        if i in old and isinstance(message, ToolMessage) and len(note) < len(str(message.content)):
            sent.append(ToolMessage(content=note, tool_call_id=message.tool_call_id, name=message.name))
        else:
            sent.append(message)
    return sent, len(old)


def _usage(message: AIMessage) -> tuple[int, int, int]:
    """Return a reply's input, output and cached input tokens; 0 when unknown."""
    usage = message.usage_metadata
    if not usage:
        return 0, 0, 0
    cached = (usage.get("input_token_details") or {}).get("cache_read") or 0
    return usage["input_tokens"], usage["output_tokens"], cached


async def write_checks(
    llm: BaseChatModel,
    repo: Repository,
    claims: list[ClaimInput],
    budget: Budget | None = None,
    code_tools: bool = False,
    hints: bool = False,
) -> BatchResult:
    """Run the agent on one batch of claims and return its checks, run once, within the batch's budget.

    The agent submits claims as it finishes them, in any number per call; the batch ends once every claim is in. A
    submitted check that does not hold goes back once with what it saw, unless its why starts with "drift:".

    Parameters
    ----------
    llm :
        A chat model that supports tool calls.
    repo :
        The repository the claims describe.
    claims :
        The batch; labels must be unique.
    budget :
        What the batch may spend; the default when None.
    code_tools :
        Also give the agent CodeSearch (an ast-grep pattern in, matches out) and Outline (a file's functions and
        classes, or a YAML file's keys, with their lines).
    hints :
        Add to the prompt the pattern and query syntax that most often fails.
    """
    budget = budget or Budget()
    by_label = {c.label: c for c in claims}
    tools = TOOLS | (CODE_TOOLS if code_tools else {})
    prompt = PROMPT + ("\n" + CODE_TOOLS_NOTE if code_tools else "") + ("\n\n" + HINTS if hints else "")
    model = llm.bind_tools(list(tools.values()))
    # The final turn asks for a Submit as structured output: some providers ignore a forced tool choice.
    last_call = llm.with_structured_output(Submit, method="function_calling", include_raw=True)
    history: list[BaseMessage] = [SystemMessage(prompt), HumanMessage(_message(claims))]
    result = BatchResult()
    done: set[str] = set()
    sent_back: set[str] = set()
    warned = False
    last_cost = growth = 0  # the last call's tokens and how much more it cost than the one before
    while done != set(by_label):
        near_end = (
            result.turns >= budget.max_turns - 2 or result.tokens_in + result.tokens_out >= 0.8 * budget.max_tokens
        )
        if near_end and not warned:
            open_ = ", ".join(sorted(set(by_label) - done))
            history.append(
                HumanMessage(
                    f"Budget nearly spent: Submit now for every open claim ({open_}): the checks you have, and a "
                    "reason for any claim you could not check."
                )
            )
            warned = True
        if result.turns and result.turns % REMIND_EVERY == 0 and not near_end:
            open_ = ", ".join(sorted(set(by_label) - done))
            history.append(
                HumanMessage(f"Still open: {open_}. Submit now each claim you already have a check or reason for.")
            )
        sent, result.trimmed = _trimmed(history) if budget.trim else (list(history), 0)
        result.chars_sent += sum(len(str(m.content)) for m in sent)
        result.chars_untrimmed += sum(len(str(m.content)) for m in history)
        spent = result.tokens_in + result.tokens_out
        if result.turns >= budget.max_turns - 1 or spent + last_cost + growth >= budget.max_tokens:
            # The last call: by turns, or because the next call, guessed as the last plus its growth (each call
            # sends the whole history), would pass the token budget. The guess can fall short; see Budget.
            await _final(last_call, sent, repo, by_label, done, sent_back, result)
            if done != set(by_label):
                result.stopped = f"budget spent: {result.turns} turns, {result.tokens_in + result.tokens_out} tokens"
            break
        reply = await model.ainvoke(sent)
        assert isinstance(reply, AIMessage)
        result.turns += 1
        tokens_in, tokens_out, cached = _usage(reply)
        result.tokens_in += tokens_in
        result.tokens_out += tokens_out
        result.tokens_cached += cached
        growth = max(tokens_in + tokens_out - last_cost, 0) if last_cost else 0
        last_cost = tokens_in + tokens_out
        history.append(reply)
        if not reply.tool_calls:
            history.append(HumanMessage("Use the tools; Submit each claim when it is ready."))
            continue
        for call in reply.tool_calls:
            name, args, call_id = call["name"], call["args"], call["id"] or ""
            asked = json.dumps(args)[:200]
            if name == "Submit":
                try:
                    submission = Submit.model_validate(args)
                except ValidationError as error:
                    content = f"Submit was not valid, fix it and submit again: {error}"[:MAX_CHARS]
                else:
                    content = _take(repo, submission, by_label, done, sent_back, near_end, result)
            elif name in tools:
                try:
                    content = _tool(repo, name, args)
                except (ValidationError, re.error, OSError, ValueError, RuntimeError) as error:
                    content = f"{name} failed: {type(error).__name__}: {error}"[:MAX_CHARS]
            else:
                content = f"No tool called {name}."
            result.calls.append(f"{result.turns}. {name} {asked[:120]} -> {content[:160]}")
            history.append(
                ToolMessage(content=content, tool_call_id=call_id, name=name, additional_kwargs={"asked": asked})
            )
    result.unfinished = [c.claim_id for c in claims if c.label not in done]
    if result.stopped:
        log.warning("batch_stopped", reason=result.stopped, unfinished=len(result.unfinished))
    return result


async def _final(
    last_call: Any,
    sent: list[BaseMessage],
    repo: Repository,
    by_label: dict[str, ClaimInput],
    done: set[str],
    sent_back: set[str],
    result: BatchResult,
) -> None:
    """Make the batch's last call, which can only answer with a Submit, and record what it holds.

    A Submit among other tool calls in the reply is read even when the reply as a whole is not (the model sometimes
    calls TryCheck as well). With no readable Submit, or one that names none of the open claims, the call is made
    once more, saying only Submit exists now.
    """
    open_ = ", ".join(sorted(set(by_label) - done))
    ask = f"Last call: submit every open claim ({open_}), a check where you have one, else a reason."
    error = ""
    for attempt in range(2):
        if attempt:
            ask = f"Only the Submit tool exists now; your last answer could not be read ({error[:200]}). {ask}"
        output = await last_call.ainvoke([*sent, HumanMessage(ask)])
        result.turns += 1
        raw = output.get("raw")
        submission = output.get("parsed")
        if isinstance(raw, AIMessage):
            tokens_in, tokens_out, cached = _usage(raw)
            result.tokens_in += tokens_in
            result.tokens_out += tokens_out
            result.tokens_cached += cached
            if not isinstance(submission, Submit):
                submission = _submit_in(raw)
        if isinstance(submission, Submit):
            named = {c.claim for c in submission.checks} | {n.claim for n in submission.no_checks}
            if named & (set(by_label) - done):
                content = _take(repo, submission, by_label, done, sent_back, True, result)
                result.calls.append(f"{result.turns}. final Submit -> {content[:160]}")
                return
            error = "the Submit names none of the open claims"
        else:
            error = str(output.get("parsing_error"))
        result.calls.append(f"{result.turns}. final Submit -> no readable Submit: {error[:160]}")


def _submit_in(reply: AIMessage) -> Submit | None:
    """Return the first readable Submit among a reply's tool calls, or None."""
    for call in reply.tool_calls:
        if call["name"] == "Submit":
            try:
                return Submit.model_validate(call["args"])
            except ValidationError:
                continue
    return None


def _take(
    repo: Repository,
    submission: Submit,
    by_label: dict[str, ClaimInput],
    done: set[str],
    sent_back: set[str],
    near_end: bool,
    result: BatchResult,
) -> str:
    """Record the submitted claims still open and return what the agent is told.

    A check that does not hold is sent back once, with what its steps saw, unless it is marked drift or the budget
    is nearly spent; sent back a second time it is recorded as it is. Labels not in the batch, or already recorded,
    are ignored.
    """
    taken, returned = [], []
    for check in submission.checks:
        if check.claim not in by_label or check.claim in done:
            continue
        holds, results = run_check(repo, check.steps)
        drift = check.why.lower().startswith("drift:")
        if not holds and not drift and not near_end and check.claim not in sent_back:
            sent_back.add(check.claim)
            returned.append(f"{check.claim}: " + "; ".join(r.detail[:200] for r in results if not r.holds))
            continue
        result.checks.append(WrittenCheck(by_label[check.claim].claim_id, check, holds, results))
        done.add(check.claim)
        taken.append(check.claim)
    for no_check in submission.no_checks:
        if no_check.claim in by_label and no_check.claim not in done:
            result.no_checks[by_label[no_check.claim].claim_id] = no_check.reason
            done.add(no_check.claim)
            taken.append(no_check.claim)
    lines = [f"Recorded: {', '.join(taken) or 'none'}."]
    if returned:
        lines.append(
            "Sent back, these checks do not hold now. Either the check is wrong (too wide, the wrong file, a guess) "
            "and you fix it, or the claim is wrong and you submit it again with a why starting 'drift:':"
        )
        lines += returned
    open_ = sorted(set(by_label) - done)
    lines.append(f"Still open: {', '.join(open_)}." if open_ else "Every claim is in.")
    return "\n".join(lines)[:MAX_CHARS]
