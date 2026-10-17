"""Plant three false claims in each of three clones of kmctl main, run the
three draft audit prompts live (Gemini 3.8 Flash), and score each report.

Exit 0 only when every audit ran and caught 3 of 3 plants (risks 1 and 2 do
not hold); exit 1 otherwise.
Usage: python runner.py WORKDIR [AUDIT ...]   (AUDIT: docs okf docsokf)
"""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT = HERE / "agent.py"
SOURCE = "/home/vscode/kmctl"

PLANTS = {
    "docs": [
        (
            "docs/reference/commands.md",
            "| `--by NEW` | The number of the decision that replaces it. Required. | |",
            "| `--with NEW` | The number of the decision that replaces it. Required. | |",
            "flag rename: decision supersede --by -> --with (truth: src/kmctl/__init__.py)",
        ),
        (
            "docs/how-to/install-the-plugin-and-the-ci-action.md",
            "opens or updates the issue; default `high` |",
            "opens or updates the issue; default `medium` |",
            "min_severity default high -> medium (truth: action.yml, action/agent.py)",
        ),
        (
            "docs/how-to/install-the-plugin-and-the-ci-action.md",
            "from running the script the action runs, `action/knowledge-ci.sh`, locally,",
            "from running the script the action runs, `action/run-checks.sh`, locally,",
            "missing path: action/run-checks.sh (real: action/knowledge-ci.sh)",
        ),
    ],
    "okf": [
        (
            ".okf/manifesto.md",
            "Status: enforced by `tests/test_briefing.py::test_briefing_token_budget`.",
            "Status: enforced by `tests/test_budget.py::test_briefing_token_budget`.",
            "invariant I3 names a test file that does not exist: tests/test_budget.py",
        ),
        (
            ".okf/decisions/0017-the-ci-audit-is-a-standalone-pydanticai-agent-script.md",
            "`--min-severity` (default high). On an update",
            "`--min-severity` (default medium). On an update",
            "decision default: --min-severity default high -> medium (truth: action/agent.py)",
        ),
        (
            ".okf/architecture/overview.md",
            "`scripts/sync_antigravity_rules.py` writes the Antigravity copies",
            "`scripts/copy_antigravity_rules.py` writes the Antigravity copies",
            "architecture names a missing file: scripts/copy_antigravity_rules.py",
        ),
    ],
    "docsokf": [
        (
            "docs/explanation/why-one-hook-and-report-only-audits.md",
            'limit, and its findings go to the job summary and one "Knowledge audit" issue.',
            'limit, and its findings go to the job summary and one "Knowledge audit" issue;\n'
            "a high finding fails the pull request's check.",
            "docs say a high audit finding fails the PR (okf: ADR 0005, 0017 report only)",
        ),
        (
            "docs/how-to/install-kmctl-with-apm.md",
            "whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart\n"
            "hook prints the kmctl briefing at the start of each session.",
            "whether to use the `okf-bundle` server from `.mcp.json`. The SessionStart\n"
            "hook prints the kmctl briefing at the start of each session, and a\n"
            "PostToolUse hook names the `.okf/` pages that describe each file the\n"
            "agent edits.",
            "docs say a second (PostToolUse) hook exists (okf: ADR 0004 one hook, nudge rejected)",
        ),
        (
            "docs/how-to/install-kmctl-with-apm.md",
            "installs, upgrades and removes it; `kmctl plugin patch` then adds what APM\n"
            "cannot install yet.",
            "installs, upgrades and removes it; `kmctl plugin patch` then adds what APM\n"
            "cannot install yet. Without APM, `kmctl plugin install --harness claude`\n"
            "installs the same package as the Claude Code plugin `kmctl@kmctl`.",
            "docs name a non-APM install route (okf: ADR 0014 APM only, 0021)",
        ),
    ],
}

PROMPTS = {
    "docs": HERE / "prompts" / "docs-vs-code.md",
    "okf": HERE / "prompts" / os.environ.get("OKF_PROMPT", "okf-vs-code.md"),
    "docsokf": HERE / "prompts" / "okf-vs-docs.md",
}


def sh(*cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def plant(name: str, copy: Path) -> list[dict]:
    sh("git", "clone", "-q", SOURCE, str(copy))
    sh("git", "config", "user.email", "spike@example.com", cwd=copy)
    sh("git", "config", "user.name", "spike", cwd=copy)
    for path, old, new, what in PLANTS[name]:
        file = copy / path
        text = file.read_text()
        assert text.count(old) == 1, (path, old)
        file.write_text(text.replace(old, new))
    record = []
    for path, old, new, what in PLANTS[name]:
        text = (copy / path).read_text()
        start = text[: text.index(new)].count("\n") + 1
        first_changed = start + next(
            i for i, (a, b) in enumerate(zip(old.splitlines() + [""], new.splitlines())) if a != b
        )
        end = start + new.count("\n")
        record.append(
            {"path": path, "line": first_changed, "span": [start, end],
             "old": old, "new": new, "what": what}
        )
    sh("git", "commit", "-qam", "docs: update", cwd=copy)
    return record


def scope(name: str, copy: Path) -> int:
    if name == "okf":
        return sum(
            1 for p in (copy / ".okf").rglob("*.md")
            if "handoffs" not in p.parts and p.name not in ("log.md",)
        )
    return sum(1 for p in (copy / "docs").rglob("*.md"))


def stats(out: Path) -> dict:
    t = out / "transcript.json"
    if not t.exists():
        return {}
    msgs = json.loads(t.read_text())
    responses = sum(1 for m in msgs if m.get("kind") == "response")
    retries = sum(
        1 for m in msgs if m.get("kind") == "request"
        for p in m.get("parts", [])
        if p.get("part_kind") == "retry-prompt" and not p.get("tool_name")
        or p.get("part_kind") == "retry-prompt" and p.get("tool_name") == "final_result"
    )
    tools: dict[str, int] = {}
    for m in msgs:
        for p in m.get("parts", []):
            if p.get("part_kind") == "tool-call":
                tools[p["tool_name"]] = tools.get(p["tool_name"], 0) + 1
    shell = [
        json.loads(p["args"]) if isinstance(p["args"], str) else p["args"]
        for m in msgs for p in m.get("parts", [])
        if p.get("part_kind") == "tool-call" and p.get("tool_name") == "run_shell"
    ]
    return {"requests": responses, "output_retries": retries, "tool_calls": tools,
            "shell_commands": [s.get("command") for s in shell]}


def parse_cite(c: str):
    c = c.strip().strip("`")
    path, _, lines = c.rpartition(":")
    a, _, b = lines.partition("-")
    try:
        return path.lstrip("./") if path.startswith("./") else path, int(a), int(b or a)
    except ValueError:
        return c, 0, 0


def score(name: str, copy: Path, out: Path, plants: list[dict], code: int) -> dict:
    result = {"audit": name, "exit": code, "scope": scope(name, copy), **stats(out)}
    rep = out / "report.json"
    if not rep.exists():
        result.update(caught=0, plants=[{"what": p["what"], "caught": False} for p in plants])
        return result
    report = json.loads(rep.read_text())
    findings = report["findings"]
    used = set()
    pres = []
    for p in plants:
        hit = None
        for i, f in enumerate(findings):
            path, a, b = parse_cite(f["claim"])
            if path == p["path"] and a <= p["span"][1] + 2 and b >= p["span"][0] - 2:
                hit = i
                break
        if hit is not None:
            used.add(hit)
        pres.append({"what": p["what"], "at": f'{p["path"]}:{p["line"]}',
                     "caught": hit is not None,
                     "finding": findings[hit] if hit is not None else None})
    result.update(
        caught=sum(p["caught"] for p in pres),
        plants=pres,
        findings=len(findings),
        checked=len(report["checked"]),
        checked_subjects=[c["subject"] for c in report["checked"]],
        other_findings=[f for i, f in enumerate(findings) if i not in used],
        summary=report["summary"],
    )
    return result


def run_one(name: str, work: Path, key: str) -> dict:
    copy = work / f"copy-{name}"
    out = work / f"out-{name}"
    plants = plant(name, copy)
    (work / f"plants-{name}.json").write_text(json.dumps(plants, indent=2))
    env = {k: v for k, v in os.environ.items() if k not in ("GH_TOKEN", "GITHUB_TOKEN")}
    env["AUDIT_API_KEY"] = key
    with open(work / f"log-{name}.txt", "w") as log:
        code = subprocess.run(
            ["uv", "run", "--script", str(AGENT), "run", "--model", "gemini-3.8-flash",
             "--base-url", "https://generativelanguage.googleapis.com/v1beta/openai/",
             "--api-key-env", "AUDIT_API_KEY", "--timeout", "25m", "--repo", str(copy),
             "--prompt-file", str(PROMPTS[name]), "--out", str(out)],
            cwd=copy, env=env, stdout=log, stderr=subprocess.STDOUT,
        ).returncode
    return score(name, copy, out, plants, code)


def main() -> int:
    work = Path(sys.argv[1]).resolve()
    names = sys.argv[2:] or ["docs", "okf", "docsokf"]
    work.mkdir(parents=True, exist_ok=False)
    key = subprocess.run(
        ["bash", "-ic", 'printf %s "$GEMINI_API_KEY"'],
        capture_output=True, text=True,
    ).stdout
    assert key, "no GEMINI_API_KEY"
    with ThreadPoolExecutor(len(names)) as pool:
        results = list(pool.map(lambda n: run_one(n, work, key), names))
    (work / "results.json").write_text(json.dumps(results, indent=2))
    ok = True
    for r in results:
        print(f"== {r['audit']}: exit {r['exit']}, caught {r['caught']}/3, "
              f"findings {r.get('findings')}, checked {r.get('checked')} of {r['scope']} in scope, "
              f"requests {r.get('requests')}, output retries {r.get('output_retries')}")
        print(f"   tools: {r.get('tool_calls')}")
        print(f"   shell: {r.get('shell_commands')}")
        for p in r["plants"]:
            f = p.get("finding")
            print(f"   [{'CAUGHT' if p['caught'] else 'MISSED'}] {p['what']} @ {p.get('at')}")
            if f:
                print(f"       claim {f['claim']} vs {f['contradicted_by']}: {f['title']}")
        for f in r.get("other_findings", []):
            print(f"   [OTHER {f['severity']}] {f['claim']} vs {f['contradicted_by']}: {f['title']}")
        print(f"   checked: {r.get('checked_subjects')}")
        ok = ok and r["exit"] == 0 and r["caught"] == 3
    print(f"results: {work / 'results.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
