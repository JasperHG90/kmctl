"""Measure what kmctl's audit agents and session context cost in tokens, from real runs.

Run from the repository root:

    uv run python .okf/prototypes/token-costs/measure.py SUBAGENTS_DIR

SUBAGENTS_DIR is a Claude Code session's ``subagents/`` folder (under
``~/.claude/projects/<project>/<session>/``). The script reads each agent's
transcript, keeps the claims extractor and check writer runs (told apart by
their first prompt), sums the tokens of each distinct API message, and reads
how much work the agent reported in its summary line. It writes
``agents.csv`` (one row per agent, counts only, no transcript text) and
prints the per-unit totals. It also measures, in characters, what kmctl puts
into every session's context: the briefing and the four knowledge rules.
"""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KINDS = {
    "You are the kmctl-claims-extractor": "extractor",
    "You are the kmctl-check-writer": "writer",
}
SECTIONS = re.compile(r"sections stored:\s*(\d+)\s*\(claims:([^)]*)\)")
CHECKS = re.compile(r"checks stored:\s*(\d+)[^\n]*?reasons:\s*(\d+)")
NUMBER = re.compile(r"(\d+)")
#: USD per million tokens, from https://platform.claude.com/docs/en/about-claude/pricing
#: on 2026-11-12: (input, 5m cache write, 1h cache write, cache read, output).
#: Haiku 5.5 doubles to the second tier when one prompt is over 100,000 tokens.
PRICES: dict[str, list[tuple[int, tuple[float, float, float, float, float]]]] = {
    "claude-haiku-5-5": [
        (100_000, (0.10, 0.125, 0.20, 0.01, 0.50)),
        (10**12, (0.50, 0.625, 1.00, 0.05, 2.50)),
    ],
    "claude-sonnet-5-5": [(10**12, (2.0, 2.50, 4.0, 0.10, 10.0))],
    "claude-opus-5-5": [(10**12, (4.0, 5.0, 8.0, 0.20, 20.0))],
}


def cost(model: str, usage: dict[str, object]) -> float:
    """What one API message cost in USD, by its model, its prompt size tier and its cache split."""
    cache = usage.get("cache_creation") or {}
    assert isinstance(cache, dict)
    write_5m = int(cache.get("ephemeral_5m_input_tokens", 0) or 0)
    write_1h = int(cache.get("ephemeral_1h_input_tokens", 0) or 0)
    written = int(usage.get("cache_creation_input_tokens", 0) or 0)
    if write_5m + write_1h < written:  # no split recorded: count it as 5m
        write_5m = written - write_1h
    fresh = int(usage.get("input_tokens", 0) or 0)
    read = int(usage.get("cache_read_input_tokens", 0) or 0)
    out = int(usage.get("output_tokens", 0) or 0)
    prompt = fresh + written + read
    tiers = PRICES.get(model)
    if tiers is None:
        return 0.0
    rate = next(r for limit, r in tiers if prompt <= limit)
    return (
        fresh * rate[0]
        + write_5m * rate[1]
        + write_1h * rate[2]
        + read * rate[3]
        + out * rate[4]
    ) / 1e6


def _kind(first_prompt: str) -> str | None:
    """Which audit agent a transcript belongs to, from its first prompt."""
    for start, kind in KINDS.items():
        if first_prompt.startswith(start):
            return kind
    return None


def _units(kind: str, text: str) -> tuple[int, int]:
    """(sections, claims answered) from the last summary line in the agent's transcript.

    The summary arrives in the hand-back call, so the whole transcript is
    searched; the patterns need digits, so the instructions' "N" template
    never matches.

    For the extractor, claims are those it stored (the counts per kind);
    for the writer, claims answered are checks plus reasons. A writer whose
    summary counts checks including reasons is read as written.
    """
    if kind == "extractor":
        hits = SECTIONS.findall(text)
        if not hits:
            return 0, 0
        stored, kinds = hits[-1]
        return int(stored), sum(int(n) for n in NUMBER.findall(kinds))
    checks = CHECKS.findall(text)
    return (0, int(checks[-1][0]) + int(checks[-1][1])) if checks else (0, 0)


def read_agent(path: Path) -> dict[str, object] | None:
    """One audit agent's token totals and reported work, or None for any other agent."""
    lines = []
    for line in path.read_text().splitlines():
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a transcript still being written ends in a partial line
    first = next((r for r in lines if r.get("type") == "user"), None)
    content = (first or {}).get("message", {}).get("content", "")
    kind = _kind(content if isinstance(content, str) else "")
    if kind is None:
        return None
    seen: dict[str, dict[str, int]] = {}
    for record in lines:
        message = record.get("message", {})
        if record.get("type") != "assistant" or not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if usage and message.get("id"):
            # one message is logged once per content block; keep its model for pricing
            seen[message["id"]] = {**usage, "_model": message.get("model", "")}
    sections, claims = _units(kind, path.read_text().replace("\\n", "\n"))
    total = {
        k: sum(u.get(k, 0) for u in seen.values())
        for k in (
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "output_tokens",
        )
    }
    over = sum(
        1
        for u in seen.values()
        if int(u.get("input_tokens", 0))
        + int(u.get("cache_creation_input_tokens", 0))
        + int(u.get("cache_read_input_tokens", 0))
        > 100_000
    )
    return {
        "agent": path.stem.removeprefix("agent-"),
        "kind": kind,
        "messages": len(seen),
        "messages_over_100k": over,
        **total,
        "usd": round(sum(cost(str(u["_model"]), u) for u in seen.values()), 4),
        "sections": sections,
        "claims": claims,
    }


def context_chars(root: Path) -> dict[str, int]:
    """Characters kmctl adds to every session: the briefing, and the knowledge rules APM installs."""
    briefing = subprocess.run(
        ["uv", "run", "kmctl", "briefing"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    rules = sorted((root / "apm" / "claude" / ".apm" / "instructions").glob("*.md"))
    skills = {
        p.parent.name: len(p.read_text())
        for p in sorted((root / "apm" / ".apm" / "skills").glob("*/SKILL.md"))
    }
    return {
        "briefing": len(briefing),
        "knowledge rules": sum(len(p.read_text()) for p in rules),
        "knowledge rule files": len(rules),
        **{f"skill {name}": n for name, n in skills.items()},
    }


def main(folder: Path) -> None:
    """Write agents.csv and print per-unit token totals."""
    rows = [r for p in sorted(folder.glob("agent-*.jsonl")) if (r := read_agent(p))]
    with (HERE / "agents.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for kind, unit in (("extractor", "sections"), ("writer", "claims")):
        done = [r for r in rows if r["kind"] == kind and r[unit]]
        units = sum(int(r[unit]) for r in done)
        print(f"{kind}: {len(done)} runs with a summary, {units} {unit}")
        for key in (
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
            "output_tokens",
        ):
            total = sum(int(r[key]) for r in done)
            print(f"  {key}: {total:,} total, {total / units:,.0f} per {unit[:-1]}")
        usd = sum(float(r["usd"]) for r in done)
        over = sum(int(r["messages_over_100k"]) for r in done)
        msgs = sum(int(r["messages"]) for r in done)
        print(f"  cost: ${usd:.2f} total, ${usd / units:.4f} per {unit[:-1]}")
        print(f"  messages: {msgs:,}, of which {over:,} had prompts over 100K tokens")
        if kind == "extractor":
            claims = sum(int(r["claims"]) for r in done)
            print(f"  claims stored: {claims} ({claims / units:.1f} per section)")
    print("per-session context, characters:", context_chars(Path.cwd()))


if __name__ == "__main__":
    main(Path(sys.argv[1]).expanduser())
