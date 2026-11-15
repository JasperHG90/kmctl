"""Pilot: which decision-model questions tell the extractor and the router something, scored against labels we have.

Run from the audit-cli folder, with the shell's keys loaded:

    uv run python scripts/pilots/questions.py ask [MODEL]     # ollama/clef:27b (default) or jev-latest
    uv run python scripts/pilots/questions.py score [MODEL]   # no calls: score the saved answers

Before extraction, every sentence of the 26 hand-labelled sections (../audit-agent/gold.jsonl) is asked:

- specific (score): names nothing, a part, a file or symbol, or a value;
- restates (noul): says again what an earlier sentence of the section said;
- audience (choice): users, maintainers, agents, or no one in particular;
- when (choice): the repository now, history, a rule for people, an intent, or an outside tool;
- checkable (noul): could the repository's files confirm it (the plain question, as a baseline);
- kind (choice): the extractor's six kinds.

They are scored against the hand labels: whether the sentence holds a claim, whether that claim is checkable (point or
structural), its kind, and its quantifier (../audit-agent/gold_quantifiers.json: exists, all, none).

For routing, every stored claim is asked, with the other claims of its section:

- negative (noul): says something never happens, is absent, or happens only one way;
- scope (choice): holds at one place, for every member of a list, or across the whole system;
- names (choice): a file, a symbol, a flag, a config or workflow key, a dependency, or nothing;
- depends (noul): is true only if another claim of the section is;
- stakes (score): cosmetic, misleading, or harmful if wrong.

They are scored against the quantifier of the claim's sentence (82 claims sit in labelled sections), against the
checks the one-call pilots wrote (a negative step, ``expect: every``, the step ops used), and against whether that
check holds. Writes results/pilots/questions-<model>.json (answers) and questions-<model>-score.json.
"""

import asyncio
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any

import httpx

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pilots import common  # the scripts folder is not a package on the path

AGENT = common.HERE.parent / "audit-agent"
MAX_CONCURRENT = 4
CHECKABLE = {"point", "structural"}
SENTENCE = {
    "specific": {
        "type": "score",
        "instructions": "How specific is the sentence about the repository?",
        "criteria": [
            "names nothing in the repository",
            "names a part or area (the CLI, the audit, the action)",
            "names a file, command, function or setting",
            "names a value: a default, a number, a flag's effect, an exit code",
        ],
    },
    "restates": {
        "type": "noul",
        "instructions": "Does the sentence only say again what an earlier sentence of the section already said?",
    },
    "audience": {
        "type": "choice",
        "instructions": "Who is the sentence written for?",
        "criteria": {
            "users": "people who install or run the tool",
            "maintainers": "people who change the tool's code",
            "agents": "AI agents working in the repository",
            "anyone": "no one in particular: background, history or reasons",
        },
    },
    "when": {
        "type": "choice",
        "instructions": "What is the sentence about?",
        "criteria": {
            "current": "what the repository's code, configuration or files do or hold now",
            "history": "what happened, was tried, decided or replaced before",
            "rule": "a rule, habit or duty for people or agents",
            "intent": "a purpose, audience or reason",
            "outside": "what a tool, service or platform outside the repository does on its own",
        },
    },
    "checkable": {
        "type": "noul",
        "instructions": "Could reading the repository's own files (code, configuration, workflows, tests) confirm "
        "or refute the sentence? Documents that restate it do not count.",
    },
    "kind": {
        "type": "choice",
        "instructions": "Which kind of claim does the sentence make?",
        "criteria": {
            "point": "one specific fact you can check at one place: a value, a name, a default, a flag, a file",
            "structural": "how parts relate, or a fact about every member of a set you can list",
            "broad": "a sweeping statement about the whole system with no list to go through",
            "subjective": "a value judgement or opinion",
            "external": "a fact about something outside the repository",
            "none": "no claim about the repository at all",
        },
    },
}
CLAIM = {
    "negative": {
        "type": "noul",
        "instructions": "Does the claim say something never happens, is absent, or happens only one way (never, no, "
        "only, not)?",
    },
    "scope": {
        "type": "choice",
        "instructions": "Where must the repository look a certain way for the claim to be true?",
        "criteria": {
            "one": "at one place: one file, one setting, one function",
            "every": "at every member of a list you can go through: every workflow, every command",
            "whole": "across the whole system, with no list to go through",
        },
    },
    "names": {
        "type": "choice",
        "instructions": "What does the claim name that a check would look at?",
        "criteria": {
            "file": "a file or folder",
            "symbol": "a function, class or variable in code",
            "flag": "a command or a command-line flag",
            "config": "a key in a configuration or workflow file",
            "dependency": "a package or module the code uses",
            "nothing": "nothing a check could look at",
        },
    },
    "depends": {
        "type": "noul",
        "instructions": "Is the claim true only if another claim of the same section (listed under 'others') is?",
    },
    "stakes": {
        "type": "score",
        "instructions": "If the claim were false, how much would it hurt someone who believed it?",
        "criteria": [
            "cosmetic: nothing breaks",
            "misleading: someone wastes time or does the wrong thing",
            "harmful: a security hole, lost data or a broken release",
        ],
    },
}
NEGATIVE_KEYS = {"present", "exists", "defined", "imported"}
OP_FOR_NAMES = {
    "file": {"file"},
    "symbol": {"definition", "grep"},
    "flag": {"help", "grep"},
    "config": {"query"},
    "dependency": {"imports", "query"},
}


def gold_sentences() -> list[dict[str, Any]]:
    """Return every sentence of the labelled sections, with its earlier sentences and its hand labels."""
    chunks = {c["id"]: c for c in map(json.loads, (AGENT / "chunks.jsonl").read_text().splitlines())}
    quantifiers = {
        (q["id"], q["n"]): q["quantifiers"] for q in json.loads((AGENT / "gold_quantifiers.json").read_text())
    }
    rows = []
    for record in map(json.loads, (AGENT / "gold.jsonl").read_text().splitlines()):
        chunk = chunks.get(record["id"])
        if chunk is None:
            continue
        labels = {int(n): set(kinds) for n, kinds in record["labels"].items()}
        for n, sentence in enumerate(chunk["sentences"], 1):
            kinds = labels.get(n, {"none"})
            rows.append(
                {
                    "id": f"{record['id']}|{n}",
                    "state": {
                        "concept": chunk["title"],
                        "section": chunk["section"],
                        "earlier": " ".join(chunk["sentences"][max(0, n - 6) : n - 1]) or "(first sentence)",
                        "sentence": sentence,
                    },
                    "kinds": sorted(kinds),
                    "quantifiers": quantifiers.get((record["id"], n), []),
                }
            )
    return rows


def claim_states() -> list[dict[str, Any]]:
    """Return every stored claim with its sentence and the other claims of its section."""
    claims = common.claims()
    by_chunk: dict[str, list[str]] = defaultdict(list)
    for c in claims:
        by_chunk[c.chunk_id].append(c.text)
    return [
        {
            "id": c.claim_id,
            "gold_key": f"{c.chunk_id}|{c.n}",
            "state": {
                "claim": c.text,
                "sentence": c.sentence,
                "from": c.chunk_id,
                "others": [t for t in by_chunk[c.chunk_id] if t != c.text][:12],
            },
        }
        for c in claims
    ]


async def ask(model: str) -> None:
    """Ask both question sets and save the answers, skipping items already answered by this model."""
    path = common.OUT / f"questions-{common.slug(model)}.json"
    saved: dict[str, Any] = json.loads(path.read_text()) if path.exists() else {"sentences": {}, "claims": {}}
    todo = [("sentences", r, SENTENCE) for r in gold_sentences() if r["id"] not in saved["sentences"]]
    todo += [("claims", r, CLAIM) for r in claim_states() if r["id"] not in saved["claims"]]
    ledger = common.Ledger()
    if model == common.JEV:
        ledger.check(jev_calls=len(todo))
    limit = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient(timeout=180) as client:

        async def one(group: str, row: dict[str, Any], questions: dict[str, Any]) -> None:
            """Ask one item its questions; a failed call leaves it unanswered for the next run."""
            async with limit:
                try:
                    saved[group][row["id"]] = await common.decide(client, model, row["state"], questions)
                except httpx.HTTPError as error:
                    failed.append(f"{row['id']}: {error}"[:200])

        failed: list[str] = []
        await asyncio.gather(*(one(*t) for t in todo))
    if model == common.JEV:
        ledger.add("questions", jev_calls=len(todo))
    common.OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(saved, indent=1))
    print(f"{model}: asked {len(todo)}, {len(failed)} failed", *failed[:5], sep="\n")


def auc(scores: list[float], labels: list[bool]) -> float | None:
    """Return the chance a random positive scores above a random negative (0.5 is no signal), or None."""
    pos = [s for s, y in zip(scores, labels, strict=True) if y]
    neg = [s for s, y in zip(scores, labels, strict=True) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 2)


def expected(levels: dict[str, float]) -> float:
    """Return a score answer's expected level."""
    return sum(int(k) * v for k, v in levels.items())


def argmax(probabilities: dict[str, float]) -> str:
    """Return the most likely option of a choice."""
    return max(probabilities, key=lambda k: probabilities[k])


def by_option(options: list[str], labels: list[bool]) -> dict[str, str]:
    """Return, per chosen option, how many items had the label: 'k of n'."""
    table: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for option, label in zip(options, labels, strict=True):
        table[option][0] += label
        table[option][1] += 1
    return {o: f"{k} of {n}" for o, (k, n) in sorted(table.items(), key=lambda kv: -kv[1][1])}


def outcomes() -> dict[str, dict[str, Any]]:
    """Return each claim's one-call result (grouped first, then single): status and check, for claims that got one."""
    found: dict[str, dict[str, Any]] = {}
    for name in ("oneshot-lines-single-low", "oneshot-lines-grouped-low"):  # grouped wins where both answered
        for cid, entry in json.loads((common.OUT / f"{name}.json").read_text())["claims"].items():
            if entry["status"] != "unanswered":
                found[cid] = entry
    return found


def gates(answers: list[dict[str, Any]], checkable: list[bool]) -> dict[str, dict[str, Any]]:
    """Return, per rule for dropping a sentence before extraction, how many it drops and checkable claims it loses."""
    rules: dict[str, Callable[[dict[str, Any]], bool]] = {
        "when is not current": lambda x: argmax(x["when"]) != "current",
        "kind is none": lambda x: argmax(x["kind"]) == "none",
        "checkable below 0.5": lambda x: x["checkable"] < 0.5,
        "checkable below 0.2": lambda x: x["checkable"] < 0.2,
        "current below 0.2": lambda x: x["when"]["current"] < 0.2,
        "not current and checkable below 0.5": lambda x: argmax(x["when"]) != "current" and x["checkable"] < 0.5,
    }
    out = {}
    for name, drop in rules.items():
        dropped = [c for x, c in zip(answers, checkable, strict=True) if drop(x)]
        out[name] = {
            "dropped": f"{len(dropped)} of {len(answers)}",
            "checkable_lost": f"{sum(dropped)} of {sum(checkable)}",
        }
    return out


def score_sentences(answers: dict[str, Any]) -> dict[str, Any]:
    """Score the before-extraction answers against the hand labels."""
    rows = [r for r in gold_sentences() if r["id"] in answers]
    clear = [r for r in rows if not ({"none"} < set(r["kinds"]))]  # "none or point" is left out of yes/no targets
    has_claim = [r["kinds"] != ["none"] for r in clear]
    checkable = [bool(set(r["kinds"]) & CHECKABLE) for r in clear]
    a = [answers[r["id"]] for r in clear]
    quantified = [r for r in rows if r["quantifiers"]]
    kind_hits = sum(argmax(answers[r["id"]]["kind"]) in r["kinds"] for r in rows)
    return {
        "sentences": len(rows),
        "clear_labels": len(clear),
        "has_claim": sum(has_claim),
        "checkable": sum(checkable),
        "auc_has_claim": {
            "specific": auc([expected(x["specific"]) for x in a], has_claim),
            "checkable": auc([x["checkable"] for x in a], has_claim),
            "restates (low is a claim)": auc([-x["restates"] for x in a], has_claim),
            "when=current": auc([x["when"]["current"] for x in a], has_claim),
            "kind not none": auc([1 - x["kind"]["none"] for x in a], has_claim),
        },
        "auc_checkable": {
            "specific": auc([expected(x["specific"]) for x in a], checkable),
            "checkable": auc([x["checkable"] for x in a], checkable),
            "when=current": auc([x["when"]["current"] for x in a], checkable),
            "kind point+structural": auc([x["kind"]["point"] + x["kind"]["structural"] for x in a], checkable),
            "audience=anyone (low is checkable)": auc([-x["audience"]["anyone"] for x in a], checkable),
        },
        "checkable_by_audience": by_option([argmax(x["audience"]) for x in a], checkable),
        "checkable_by_when": by_option([argmax(x["when"]) for x in a], checkable),
        "checkable_by_specific": by_option([str(round(expected(x["specific"]))) for x in a], checkable),
        "drop_before_extraction": gates(a, checkable),
        "restates_yes": sum(x["restates"] > 0.5 for x in a),
        "kind_matches_hand_label": f"{kind_hits} of {len(rows)}",
        "sentences_with_quantifiers": len(quantified),
    }


def score_claims(answers: dict[str, Any]) -> dict[str, Any]:
    """Score the routing answers against the quantifiers, the checks the one-call pilots wrote, and their outcome."""
    rows = [r for r in claim_states() if r["id"] in answers]
    quantifiers = {r["id"]: r["quantifiers"] for r in gold_sentences()}
    in_gold = [r for r in rows if quantifiers.get(r["gold_key"])]
    neg_label = ["none" in quantifiers[r["gold_key"]] for r in in_gold]
    all_label = ["all" in quantifiers[r["gold_key"]] for r in in_gold]
    done = outcomes()
    checked = [r for r in rows if r["id"] in done and "check" in done[r["id"]]]
    steps = {r["id"]: done[r["id"]]["check"]["steps"] for r in checked}
    has_negative = [any(s.get(k) is False for s in steps[r["id"]] for k in NEGATIVE_KEYS) for r in checked]
    has_every = [any(s.get("expect") == "every" for s in steps[r["id"]]) for r in checked]
    named = [argmax(answers[r["id"]]["names"]) for r in checked]
    op_match = [
        bool(OP_FOR_NAMES.get(n, set()) & {s["op"] for s in steps[r["id"]]})
        for n, r in zip(named, checked, strict=True)
    ]
    answered = [r for r in rows if r["id"] in done]
    holds = [done[r["id"]]["status"] == "holds" for r in answered]
    a = [answers[r["id"]] for r in answered]
    return {
        "claims": len(rows),
        "claims_in_labelled_sentences": len(in_gold),
        "negative_vs_quantifier_none": {
            "auc": auc([answers[r["id"]]["negative"] for r in in_gold], neg_label),
            "label_none": sum(neg_label),
        },
        "scope_vs_quantifier_all": {
            "by_option": by_option([argmax(answers[r["id"]]["scope"]) for r in in_gold], all_label),
            "auc_every": auc([answers[r["id"]]["scope"]["every"] for r in in_gold], all_label),
            "label_all": sum(all_label),
        },
        "checks_written": len(checked),
        "checks_with_negative_step": sum(has_negative),
        "checks_with_expect_every": sum(has_every),
        "negative_vs_negative_step": auc([answers[r["id"]]["negative"] for r in checked], has_negative),
        "scope_every_vs_expect_every": auc([answers[r["id"]]["scope"]["every"] for r in checked], has_every),
        "names_vs_step_op": f"{sum(op_match)} of {len(checked)} checks use the op the named thing suggests",
        "names_counts": dict(Counter(argmax(x["names"]) for x in answers.values())),
        "outcome_claims": len(answered),
        "holds": sum(holds),
        "auc_holds": {
            "negative": auc([x["negative"] for x in a], holds),
            "scope=one": auc([x["scope"]["one"] for x in a], holds),
            "names not nothing": auc([1 - x["names"]["nothing"] for x in a], holds),
            "depends (low holds)": auc([-x["depends"] for x in a], holds),
            "stakes": auc([expected(x["stakes"]) for x in a], holds),
        },
        "holds_by_scope": by_option([argmax(x["scope"]) for x in a], holds),
        "holds_by_names": by_option([argmax(x["names"]) for x in a], holds),
        "depends_yes": sum(x["depends"] > 0.5 for x in answers.values()),
        "stakes_by_level": dict(Counter(str(round(expected(x["stakes"]))) for x in answers.values())),
    }


def score(model: str) -> None:
    """Score one model's saved answers and save the result."""
    saved = json.loads((common.OUT / f"questions-{common.slug(model)}.json").read_text())
    out = {
        "model": model,
        "before_extraction": score_sentences(saved["sentences"]),
        "routing": score_claims(saved["claims"]),
    }
    (common.OUT / f"questions-{common.slug(model)}-score.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def main() -> None:
    """Run the named step for the named model."""
    common.settings()
    step = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else common.CLEF
    if step == "ask":
        asyncio.run(ask(model))
    elif step == "score":
        score(model)
    else:
        raise SystemExit(f"unknown step {step!r}: ask or score")


if __name__ == "__main__":
    main()
