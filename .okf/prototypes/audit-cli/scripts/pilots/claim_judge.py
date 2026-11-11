"""Pilot: can a decision model judge a claim straight from the lines found for it, with no check?

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/claim_judge.py twins           # DeepSeek writes a false twin of each true claim
    uv run python scripts/pilots/claim_judge.py ask [MODEL]     # ollama/clef:27b (default) or jev-latest

True claims: every claim with an exact check that holds in a saved pilot run (26), and four claims about prompt and
skill text read by hand. One false claim occurs naturally: the okf-bundle rule does not mention ``kmctl verify``.
``twins`` asks DeepSeek, in one call, for a false twin of each true claim about the same thing (a changed value,
name, count or negation) and saves results/pilots/claim-twins.json; twins are then read by hand and any that is not
plainly false is listed in results/pilots/claim-twin-labels.json and left out.

``ask`` shows each claim, true or twin, with the same lines: the settle step's or the dossier's for claims about code,
the prompt or skill file for claims about prose (which checks cannot read: markdown is left out). The model is asked
a noul ("do these lines show the claim is true?") and a choice (true, false, not shown). Scored per group (prose,
point, structural) and written to results/pilots/claim-judge-<model>.json.
"""

import asyncio
import glob
import json
import pathlib
import sys
from typing import Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common, oneshot, questions  # the scripts folder is not a package on the path

MAX_CONCURRENT = 4
PROSE = {  # claim id: (file, first line, last line) holding the text the claim is about; truth read by hand
    "1f23c8cc0e4e": ("action/agent.py", 84, 130, True),
    "76d0859336b4": (".github/prompts/issue-triage-system.md", 1, 64, True),
    "334580926c53": (".github/prompts/issue-triage-system.md", 1, 64, True),
    "bbae74db6d69": ("apm/.apm/skills/audit/SKILL.md", 1, 53, True),
    "9eeef037e770": (".claude/rules/okf-bundle.md", 1, 112, False),
}
JUDGE = {
    "shown_true": {
        "type": "noul",
        "instructions": "Do the lines shown establish that the claim is true of the repository? Lines that only "
        "mention what the claim names, without showing what it says about them, do not.",
    },
    "verdict": {
        "type": "choice",
        "instructions": "What do the lines shown say about the claim?",
        "criteria": {
            "true": "they show the claim holds",
            "false": "they show the claim does not hold: a different value, name, count, or the opposite",
            "not_shown": "they do not settle it either way",
        },
    },
}
TWIN_PROMPT = """
For each claim, write a false twin: a claim about the same thing that a reader of the same lines would find false.
Change one detail: a value, a name, a count, a file, or turn it into its opposite. Keep it as specific and as
plausible as the original; never make it vague. Answer every claim, by its label.
""".strip()


class Twin(BaseModel):
    """One claim's false twin."""

    claim: str = Field(description="The claim's label, like c3.")
    twin: str = Field(description="The false twin.")


class Twins(BaseModel):
    """A false twin for each claim shown."""

    twins: list[Twin]


def true_claims() -> list[common.StoredClaim]:
    """Return the claims taken as true: exact checks that hold in a saved run, and the prose claims read as true."""
    held: set[str] = set()
    for path in sorted(
        glob.glob(str(common.OUT / "oneshot-*.json")) + glob.glob(str(common.OUT / "agent-spend-*.json"))
    ):
        for claim_id, entry in json.loads(pathlib.Path(path).read_text()).get("claims", {}).items():
            if entry.get("status") == "holds" and entry.get("check", {}).get("strength") == "exact":
                held.add(claim_id)
    held |= {cid for cid, (*_, truth) in PROSE.items() if truth}
    return [c for c in common.claims() if c.claim_id in held]


def lines(claim: common.StoredClaim) -> str:
    """Return the lines shown for a claim: the prose file's for a prose claim, else the settle step's or dossier's."""
    if claim.claim_id in PROSE:
        path, first, last, _ = PROSE[claim.claim_id]
        text = (common.REPO / path).read_text().splitlines()
        return f"--- {path}:{first}-{last}\n" + "\n".join(f"{n}: {text[n - 1]}" for n in range(first, last + 1))
    return oneshot.lines_for(claim)


def group(claim: common.StoredClaim) -> str:
    """Return the claim's group: prose, or the extractor's kind."""
    return "prose" if claim.claim_id in PROSE else claim.kind


async def twins() -> None:
    """Ask DeepSeek for a false twin of every true claim, in one call, and save them."""
    common.settings()
    claims = true_claims()
    ledger = common.Ledger()
    ledger.check(tokens=30_000)
    labelled = {f"c{i}": c for i, c in enumerate(claims, 1)}
    text = "\n".join(f"{label}: {c.text}" for label, c in labelled.items())
    output = (
        await common.deepseek("low")
        .with_structured_output(Twins, method="function_calling", include_raw=True)
        .ainvoke([SystemMessage(TWIN_PROMPT), HumanMessage(text)])
    )
    tokens = oneshot.usage(output["raw"])
    ledger.add("claim-twins", tokens=tokens["in"] + tokens["out"])
    parsed = output["parsed"]
    assert isinstance(parsed, Twins), output.get("parsing_error")
    out = {labelled[t.claim].claim_id: {"claim": labelled[t.claim].text, "twin": t.twin} for t in parsed.twins}
    (common.OUT / "claim-twins.json").write_text(json.dumps(out, indent=1))
    for value in out.values():
        print(f"- {value['claim']}\n  > {value['twin']}")


async def ask(model: str) -> None:
    """Ask the decision model about every true claim, every kept twin and the false prose claim; score and save."""
    common.settings()
    twin_file = json.loads((common.OUT / "claim-twins.json").read_text())
    dropped = set(json.loads((common.OUT / "claim-twin-labels.json").read_text())["not_false"])
    by_id = {c.claim_id: c for c in common.claims()}
    items: list[dict[str, Any]] = []
    for claim in true_claims():
        items.append({"id": claim.claim_id, "claim": claim.text, "truth": True, "group": group(claim), "of": claim})
        if claim.claim_id in twin_file and claim.claim_id not in dropped:
            twin = twin_file[claim.claim_id]["twin"]
            items.append(
                {"id": f"{claim.claim_id}~", "claim": twin, "truth": False, "group": group(claim), "of": claim}
            )
    for claim_id, (*_, truth) in PROSE.items():
        if not truth:
            claim = by_id[claim_id]
            items.append({"id": claim_id, "claim": claim.text, "truth": False, "group": "prose", "of": claim})
    ledger = common.Ledger()
    if model == common.JEV:
        ledger.check(jev_calls=len(items))
    limit = asyncio.Semaphore(MAX_CONCURRENT)
    answers: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=180) as client:

        async def one(item: dict[str, Any]) -> None:
            """Ask about one claim."""
            state = {"claim": item["claim"], "lines": lines(item["of"])}
            async with limit:
                answers[item["id"]] = await common.decide(client, model, state, JUDGE)

        await asyncio.gather(*(one(i) for i in items))
    if model == common.JEV:
        ledger.add("claim-judge", jev_calls=len(items))
    summary: dict[str, Any] = {"model": model, "items": len(items)}
    for name in ("prose", "point", "structural", "all"):
        chosen = [i for i in items if name == "all" or i["group"] == name]
        if not chosen:
            continue
        truths = [i["truth"] for i in chosen]
        verdict = [questions.argmax(answers[i["id"]]["verdict"]) for i in chosen]
        summary[name] = {
            "true": sum(truths),
            "false": len(truths) - sum(truths),
            "auc_shown_true": questions.auc([answers[i["id"]]["shown_true"] for i in chosen], truths),
            "verdict_on_true": dict(
                __import__("collections").Counter(v for v, t in zip(verdict, truths, strict=True) if t)
            ),
            "verdict_on_false": dict(
                __import__("collections").Counter(v for v, t in zip(verdict, truths, strict=True) if not t)
            ),
        }
    out = {
        "summary": summary,
        "answers": {
            i["id"]: {"claim": i["claim"], "truth": i["truth"], "group": i["group"]} | answers[i["id"]] for i in items
        },
    }
    (common.OUT / f"claim-judge-{common.slug(model)}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "twins":
        asyncio.run(twins())
    else:
        asyncio.run(ask(sys.argv[2] if len(sys.argv) > 2 else common.CLEF))
