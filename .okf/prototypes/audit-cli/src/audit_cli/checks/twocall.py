"""The two-call writer: one call writes the checks for a group of claims from the lines found for them; after the
checks run, one more call sees only the failing checks, what each step saw, and the same lines, and fixes them.

No tools and no turns: each call is one request, so the tokens it spends are the lines and the answer, not a growing
history. Claims that read the same file go in one group. The fix call is told never to change what a check expects
to what the repository has: a check that saw the claim is false is drift, not a check to fix.
"""

import json
from dataclasses import dataclass, field
from typing import Any, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable
from pydantic import BaseModel, Field, field_validator, model_validator

from audit_cli.checks.writer import HINTS, ClaimCheck, NoCheck
from audit_cli.jsontext import read_list
from audit_cli.logs import get_logger

log = get_logger("checks.twocall")

PROMPT = (
    """
You turn claims about a repository into checks. A check is a list of steps that later runs against the repository
with no model, on every audit. A check holds when every step holds. You see each claim with the lines of the
repository already found for it; you cannot open anything else.

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
  Quote a key with a hyphen: steps[].with."persist-credentials".
- definition: a Python function, class or assigned name is defined (or not) in a glob of Python files.
- imports: a Python file imports a top-level module (or not).
- help: a command of the repository's own CLI prints --help text matching a regex (or not).

Rules:
- A check must fail if the claim were false. Test what the claim says, not a word from it.
- Scope each step to the files the claim is about, as narrowly as the lines shown allow. The knowledge itself
  (.okf/, docs/, READMEs) is never read; prompt and config files are.
- To test what code does, prefer code over grep: a call and its argument, a condition and its exit. Use grep for
  text in files no code step reads.
- Pin a regex to the code that does the thing (a condition and its exit, an argument and its default), never to a
  comment, docstring or help text that restates the claim.
- strength "exact": the steps decide the claim. "proxy": they show the code is in the shape the claim needs, but
  behaviour still has to be read.
- Give a reason instead of a check when no step can test the claim (history, intent, a rule for people, what an
  outside service does, runtime behaviour) or when the lines shown are not enough to write one: say which.
""".strip()
    + "\n\n"
    + HINTS
)

FIX = """
These checks did not hold when they ran. For each claim, either fix its check (a wrong pattern, scope or syntax),
or, if what the steps saw shows the claim is false, give the check that tests the claim with why starting "drift:",
or give a reason when no step can test it. Answer every claim. Never change what a check expects to what the
repository has: a check that saw the claim is false is drift, not a check to fix.
""".strip()


STRENGTHEN = """
These checks hold, but they would hold even if their claim were false: they did not notice the changes listed to the
code they read, or they look only for a word from the claim. For each claim, write a check that still holds on the
repository as it is now and fails when the claim is false: test the value, condition or call the claim is about, never
a name, a comment or a docstring. If no step can do better than the check you see, give the reason. Answer every
claim.
""".strip()


class Answer(BaseModel):
    """One claim's check, or the reason it has none."""

    claim: str = Field(description="The claim's label, like c1.")
    check: ClaimCheck | None = Field(default=None, description="The check, when one can be written.")
    no_check: NoCheck | None = Field(default=None, description="Otherwise, why not.")

    @model_validator(mode="before")
    @classmethod
    def _flat(cls, value: Any) -> Any:
        """Read an answer sent flat, with steps or a reason beside the label, as some models do in big groups."""
        if isinstance(value, dict) and not value.get("check") and value.get("steps"):
            check = {k: value[k] for k in ("claim", "steps", "strength", "why") if k in value}
            value = {
                **value,
                "check": check | {"strength": value.get("strength", "proxy"), "why": value.get("why", "")},
            }
        if isinstance(value, dict) and not value.get("no_check") and not value.get("check") and value.get("reason"):
            value = {**value, "no_check": {"claim": value.get("claim", ""), "reason": value["reason"]}}
        return value


class Answers(BaseModel):
    """One answer per claim shown."""

    answers: list[Answer]

    @field_validator("answers", mode="before")
    @classmethod
    def _from_text(cls, value: Any) -> Any:
        """Read a list sent as JSON text, as some models send it."""
        return read_list(value)


@dataclass
class Item:
    """One claim as shown to the writer: its label in the group, its text and sentence, and the lines found."""

    label: str
    claim_id: str
    claim: str
    sentence: str
    lines: str
    check: dict[str, Any] | None = None  # for the fix call: the check that failed
    saw: list[dict[str, Any]] = field(default_factory=list)  # for the fix call: what each step saw


@dataclass
class Spent:
    """What calls cost: how many, and their input, output and cached input tokens."""

    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_cached: int = 0

    def add(self, reply: Any) -> int:
        """Count one reply and return its tokens (input plus output)."""
        meta = getattr(reply, "usage_metadata", None) or {}
        tokens_in, tokens_out = meta.get("input_tokens", 0), meta.get("output_tokens", 0)
        self.calls += 1
        self.tokens_in += tokens_in
        self.tokens_out += tokens_out
        self.tokens_cached += (meta.get("input_token_details") or {}).get("cache_read", 0) or 0
        return int(tokens_in + tokens_out)

    @property
    def tokens(self) -> int:
        """Input plus output tokens."""
        return self.tokens_in + self.tokens_out


def write_message(items: list[Item]) -> str:
    """Build the write call's message: each claim with its sentence, then the lines found (each block once)."""
    claims = [f"{i.label}: {i.claim}\n    sentence: {i.sentence}" for i in items]
    lines = list(dict.fromkeys(i.lines for i in items))
    return "\n".join(claims) + "\n\nLines found in the repository:\n" + "\n".join(lines)


def fix_message(items: list[Item]) -> str:
    """Build the fix call's message: each claim, its check and what each step saw, then the lines found."""
    parts = [FIX, ""]
    for item in items:
        parts.append(f"{item.label}: {item.claim}\n    check: {json.dumps((item.check or {}).get('steps', []))}")
        for step, seen in zip((item.check or {}).get("steps", []), item.saw, strict=False):
            mark = "held" if seen.get("holds") else "FAILED"
            parts.append(f"    {mark}: {step.get('op')} -> {str(seen.get('detail', ''))[:300]}")
    lines = list(dict.fromkeys(i.lines for i in items))
    return "\n".join(parts) + "\n\nLines found in the repository:\n" + "\n".join(lines)


def strengthen_message(items: list[Item]) -> str:
    """Build the strengthen call's message: each claim, its holding check, what it missed, then the lines found."""
    parts = [STRENGTHEN, ""]
    for item in items:
        parts.append(f"{item.label}: {item.claim}\n    check: {json.dumps((item.check or {}).get('steps', []))}")
        parts += [f"    {str(seen.get('detail', ''))[:300]}" for seen in item.saw]
    lines = list(dict.fromkeys(i.lines for i in items))
    return "\n".join(parts) + "\n\nLines found in the repository:\n" + "\n".join(lines)


async def _ask(llm: BaseChatModel, text: str, spent: Spent) -> tuple[dict[str, Answer], int, str]:
    """Make one call and return the answers by label, the call's tokens, and why nothing was read (or "")."""
    output = cast(
        dict[str, Any],
        await llm.with_structured_output(Answers, method="function_calling", include_raw=True).ainvoke(
            [SystemMessage(PROMPT), HumanMessage(text)]
        ),
    )
    tokens = spent.add(output["raw"])
    parsed = output["parsed"]
    if not isinstance(parsed, Answers):
        return {}, tokens, str(output.get("parsing_error"))[:300]
    return {a.claim: a for a in parsed.answers}, tokens, ""


def _usable(answer: Answer | None) -> bool:
    """Whether an answer holds a check with steps or a reason."""
    return answer is not None and (bool(answer.check and answer.check.steps) or answer.no_check is not None)


@traceable(run_type="chain", name="checks: write group")
async def write_group(llm: BaseChatModel, items: list[Item], spent: Spent) -> tuple[dict[str, Answer], int]:
    """Write checks for one group; claims left unanswered are asked once more, together.

    Returns the usable answers by label and the tokens the group's calls spent.
    """
    answers, tokens, error = await _ask(llm, write_message(items), spent)
    again = [i for i in items if not _usable(answers.get(i.label))]
    if again:
        log.info("unanswered_retry", claims=[i.claim_id for i in again], error=error)
        more, more_tokens, _ = await _ask(llm, write_message(again), spent)
        answers |= {k: v for k, v in more.items() if k in {i.label for i in again}}
        tokens += more_tokens
    return {k: v for k, v in answers.items() if _usable(v)}, tokens


@traceable(run_type="chain", name="checks: fix group")
async def fix_group(llm: BaseChatModel, items: list[Item], spent: Spent) -> tuple[dict[str, Answer], int]:
    """Send one group's failing checks back once; return the usable answers by label and the tokens spent."""
    answers, tokens, _ = await _ask(llm, fix_message(items), spent)
    return {k: v for k, v in answers.items() if _usable(v)}, tokens


@traceable(run_type="chain", name="checks: strengthen group")
async def strengthen_group(llm: BaseChatModel, items: list[Item], spent: Spent) -> tuple[dict[str, Answer], int]:
    """Ask once for stronger checks for one group of weak ones; return the usable answers by label and the tokens."""
    answers, tokens, _ = await _ask(llm, strengthen_message(items), spent)
    return {k: v for k, v in answers.items() if _usable(v)}, tokens
