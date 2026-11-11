"""Pilot: write each claim's check in one model call, from the lines the settle step found, with no tools or turns.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/oneshot.py single [--effort low|default]   # one call per claim
    uv run python scripts/pilots/oneshot.py grouped                         # one call per shared file

Runs on the 19 claims the check-writer agent pilot wrote checks for (graded by hand), so the two can be compared,
or on a fixed random 30 of the claims the settle step found lines for (--sample lines), or on the 52 claims the
searching agent would get (--sample agent), shown the lines scripts/pilots/dossier.py finds for them.
Every call goes through the ledger (common.Ledger) and stops before the agreed cap. Writes
results/pilots/oneshot-<variant>.json: each claim's check or reason, whether the check holds now, and per call the
tokens, cached input tokens (prompt caching) and seconds.
"""

import argparse
import asyncio
import json
import random
import re
import sys
import time
from collections import defaultdict
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field, field_validator, model_validator

from audit_cli.checks.steps import Repository, run_check
from audit_cli.checks.writer import HINTS, ClaimCheck, NoCheck

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, dossier, no_lines  # the scripts folder is not a package on the path

PROMPT = """
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
  Quote a key with a hyphen: steps[].with."persist-credentials". Guard a function against a missing key, since
  starts_with(uses, ...) fails on a step with no uses: [?uses && starts_with(uses, 'actions/checkout')].
- definition: a Python function, class or assigned name is defined (or not) in a glob of Python files.
- imports: a Python file imports a top-level module (or not).
- help: a command of the repository's own CLI prints --help text matching a regex (or not).

Rules:
- A check must fail if the claim were false. Test what the claim says, not a word from it.
- Scope each step to the files the claim is about, as narrowly as the lines shown allow. Markdown is never read.
- To test what code does, prefer code over grep: a call and its argument, a condition and its exit. Use grep for
  text in files no code step reads.
- Pin a regex to the code that does the thing (a condition and its exit, an argument and its default), never to a
  comment, docstring or help text that restates the claim.
- strength "exact": the steps decide the claim. "proxy": they show the code is in the shape the claim needs, but
  behaviour still has to be read.
- Give a reason instead of a check when no step can test the claim (history, intent, a rule for people, what an
  outside service does, runtime behaviour) or when the lines shown are not enough to write one: say which.
""".strip()


class Answer(BaseModel):
    """One claim's check, or the reason it has none."""

    claim: str = Field(description="The claim's label, like c1.")
    check: ClaimCheck | None = Field(default=None, description="The check, when one can be written.")
    no_check: NoCheck | None = Field(default=None, description="Otherwise, why not.")

    @model_validator(mode="before")
    @classmethod
    def _flat(cls, value: Any) -> Any:
        """Read an answer the model sent flat (steps, strength, why or reason beside claim), as DeepSeek does in big
        groups."""
        if isinstance(value, dict) and not value.get("check") and value.get("steps"):
            keys = ("claim", "steps", "strength", "why")
            value = {
                **value,
                "check": {k: value[k] for k in keys if k in value}
                | {"strength": value.get("strength", "proxy"), "why": value.get("why", "")},
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
        """Read a list the model sent as JSON text, as DeepSeek sometimes does."""
        return json.loads(value) if isinstance(value, str) else value


def usage(raw: Any) -> dict[str, int]:
    """Return a reply's input, output and cached input tokens."""
    meta = getattr(raw, "usage_metadata", None) or {}
    cached = (meta.get("input_token_details") or {}).get("cache_read", 0)
    return {"in": meta.get("input_tokens", 0), "out": meta.get("output_tokens", 0), "cached": cached or 0}


def lines_for(claim: common.StoredClaim) -> str:
    """Return the lines shown for a claim: the settle step's, or for a claim it found nothing for, the dossier's."""
    found = common.snippets(claim)
    if found == "(the settle step found nothing to show)":
        found = dossier.dossier(claim)[0] or found
    return found


def files_for(claim: common.StoredClaim) -> list[str]:
    """Return the files a claim's lines come from, to group claims that share one."""
    return common.located_files(claim) or re.findall(r"^--- (\S+?):", lines_for(claim), re.MULTILINE)


def message(claims: list[tuple[str, common.StoredClaim]]) -> str:
    """Build the user message: each claim with its sentence, then the lines found for the claims."""
    lines = []
    shown: list[str] = []
    for label, claim in claims:
        lines.append(f"{label}: {claim.text}\n    sentence: {claim.sentence}")
        found = lines_for(claim)
        if found not in shown:
            shown.append(found)
    return "\n".join(lines) + "\n\nLines found in the repository:\n" + "\n".join(shown)


FIX = """
These checks did not hold when they ran. For each claim, either fix its check (a wrong pattern, scope or syntax),
or, if what the steps saw shows the claim is false, give the check that tests the claim with why starting "drift:",
or give a reason when no step can test it. Answer every claim. Never change what a check expects to what the
repository has: a check that saw the claim is false is drift, not a check to fix.
""".strip()


def fix_message(claims: list[tuple[str, common.StoredClaim]], results: dict[str, Any]) -> str:
    """Build the fix call's message: each claim, its check and what each step saw, then the lines found."""
    parts = [FIX, "", HINTS, ""]
    shown: list[str] = []
    for label, claim in claims:
        entry = results[claim.claim_id]
        parts.append(f"{label}: {claim.text}\n    check: {json.dumps(entry['check']['steps'])}")
        for step, result in zip(entry["check"]["steps"], entry["results"], strict=True):
            mark = "held" if result["holds"] else "FAILED"
            parts.append(f"    {mark}: {step['op']} -> {result['detail'][:300]}")
        found = lines_for(claim)
        if found not in shown:
            shown.append(found)
    return "\n".join(parts) + "\n\nLines found in the repository:\n" + "\n".join(shown)


def sample(name: str) -> list[common.StoredClaim]:
    """Return the graded 19, or a fixed random 30 of the claims with lines found (seed 7)."""
    claims = common.claims()
    if name == "agent":
        return no_lines.agent_share()
    if name == "graded":
        graded = set(common.graded_ids())
        return [c for c in claims if c.claim_id in graded]
    with_lines = [c for c in claims if common.snippets(c) != "(the settle step found nothing to show)"]
    return sorted(random.Random(7).sample(with_lines, 30), key=lambda c: (c.chunk_id, c.n))


async def call(
    llm: Any,
    claims: list[tuple[str, common.StoredClaim]],
    ledger: common.Ledger,
    pilot: str,
    text: str | None = None,
) -> tuple[Answers | None, dict[str, Any]]:
    """Ask for the answers to one group of claims, inside the cap; ``text`` replaces the usual user message."""
    ledger.check(tokens=6_000 * len(claims))  # a reserve: refuse before a call that could pass the cap
    started = time.monotonic()
    output = await llm.with_structured_output(Answers, method="function_calling", include_raw=True).ainvoke(
        [SystemMessage(PROMPT), HumanMessage(text or message(claims))]
    )
    sent_back = {
        str(a.get("claim")): json.dumps(a)[:400]
        for c in getattr(output["raw"], "tool_calls", None) or []
        for a in (c["args"].get("answers") if isinstance(c["args"].get("answers"), list) else [])
        if isinstance(a, dict)
    }
    tokens = usage(output["raw"])
    ledger.add(pilot, tokens=tokens["in"] + tokens["out"])
    spent: dict[str, Any] = tokens | {
        "seconds": round(time.monotonic() - started, 1),
        "claims": len(claims),
        "raw": sent_back,
    }
    if output["parsed"] is None:
        spent["parse_error"] = str(output.get("parsing_error"))[:300]
    return output["parsed"], spent


def groups(claims: list[common.StoredClaim]) -> list[list[common.StoredClaim]]:
    """Group claims by the first file the settle step found for them; claims with none go one per group."""
    by_file: dict[str, list[common.StoredClaim]] = defaultdict(list)
    alone: list[common.StoredClaim] = []
    for claim in claims:
        files = files_for(claim)
        (by_file[files[0]] if files else alone).append(claim)
    return [*by_file.values(), *([c] for c in alone)]


async def main() -> None:
    """Run one variant on the graded claims and save what it wrote and spent."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("variant", choices=["single", "grouped"])
    parser.add_argument("--effort", default="low", help="low, or default for the model's own setting.")
    parser.add_argument(
        "--sample",
        choices=["graded", "lines", "agent"],
        default="graded",
        help="graded: the 19 claims the agent pilot wrote checks for. lines: a fixed random 30 of the claims the "
        "settle step found lines for. agent: the claims the searching agent would get, with dossier lines.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Use only the first N claims of the sample.")
    parser.add_argument("--tag", default="", help="A word added to the results file name, to keep an earlier run.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="After the first answers, send each group's failing checks back once, with what their steps saw.",
    )
    args = parser.parse_args()
    common.settings()
    claims = sample(args.sample)[: args.limit or None]
    name = (
        f"oneshot-{args.sample}-{args.variant}-{args.effort}"
        + (f"-{args.limit}" if args.limit else "")
        + ("-fix" if args.fix else "")
        + (f"-{args.tag}" if args.tag else "")
    )
    llm = common.deepseek(None if args.effort == "default" else args.effort)
    ledger = common.Ledger()
    repo = Repository(common.REPO)
    batches = [[c] for c in claims] if args.variant == "single" else groups(claims)
    limit = asyncio.Semaphore(4)
    results: dict[str, Any] = {}
    calls: list[dict[str, Any]] = []

    async def one(batch: list[common.StoredClaim], retry: bool = True) -> None:
        """Answer one batch and record each claim's answer; claims left unanswered are asked once more together."""
        labelled = [(f"c{i}", c) for i, c in enumerate(batch, 1)]
        async with limit:
            try:
                parsed, spent = await call(llm, labelled, ledger, name)
            except common.CapReached as error:
                calls.append({"claims": len(batch), "error": str(error)})
                return
        raw = spent.pop("raw")
        spent["retry"] = not retry
        calls.append(spent)
        answers = {a.claim: a for a in parsed.answers} if parsed else {}
        for label, claim in labelled:
            answer = answers.get(label)
            entry: dict[str, Any] = {"claim": claim.text}
            if answer and answer.check and answer.check.steps:
                holds, steps = run_check(repo, answer.check.steps)
                entry |= {
                    "status": "holds" if holds else "fails",
                    "check": answer.check.model_dump(mode="json"),
                    "results": [s.model_dump() for s in steps],
                }
            elif answer and answer.no_check:
                entry |= {"status": "no check", "reason": answer.no_check.reason}
            else:
                why = "an answer with neither a check with steps nor a reason" if answer else "no answer for this label"
                entry |= {"status": "unanswered", "why": spent.get("parse_error") or why, "raw": raw.get(label, "")}
            results[claim.claim_id] = entry
        again = [c for _, c in labelled if results[c.claim_id]["status"] == "unanswered"]
        if retry and again:
            await one(again, retry=False)

    await asyncio.gather(*(one(b) for b in batches))
    if args.fix:
        failing = [c for c in claims if results[c.claim_id]["status"] == "fails"]

        async def fix(batch: list[common.StoredClaim]) -> None:
            """Send one group's failing checks back once and record what comes back."""
            labelled = [(f"c{i}", c) for i, c in enumerate(batch, 1)]
            async with limit:
                try:
                    parsed, spent = await call(llm, labelled, ledger, name, fix_message(labelled, results))
                except common.CapReached as error:
                    calls.append({"claims": len(batch), "error": str(error), "fix": True})
                    return
            spent.pop("raw")
            calls.append(spent | {"fix": True})
            answers = {a.claim: a for a in parsed.answers} if parsed else {}
            for label, claim in labelled:
                entry = results[claim.claim_id]
                entry["first"] = {k: entry[k] for k in ("status", "check", "results") if k in entry}
                answer = answers.get(label)
                if answer and answer.check and answer.check.steps:
                    holds, steps = run_check(repo, answer.check.steps)
                    drift = answer.check.why.lower().startswith("drift:")
                    entry |= {
                        "status": "holds" if holds else "drift" if drift else "fails",
                        "check": answer.check.model_dump(mode="json"),
                        "results": [s.model_dump() for s in steps],
                    }
                elif answer and answer.no_check:
                    for key in ("check", "results"):
                        entry.pop(key, None)
                    entry |= {"status": "no check", "reason": answer.no_check.reason}

        await asyncio.gather(*(fix(b) for b in groups(failing)))
    total = {k: sum(c.get(k, 0) for c in calls) for k in ("in", "out", "cached")}
    summary = {
        "variant": name,
        "claims": len(claims),
        "calls": len(calls),
        "tokens": total,
        "tokens_per_claim": round((total["in"] + total["out"]) / len(claims)),
        "status": dict(__import__("collections").Counter(e["status"] for e in results.values())),
        "strength": dict(
            __import__("collections").Counter(e["check"]["strength"] for e in results.values() if "check" in e)
        ),
        "ledger_total": ledger.data["tokens"],
    }
    common.OUT.mkdir(parents=True, exist_ok=True)
    (common.OUT / f"{name}.json").write_text(
        json.dumps({"summary": summary, "calls": calls, "claims": results}, indent=1)
    )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
