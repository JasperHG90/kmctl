"""r8: the worktree's real action/knowledge-audit.sh with real Hermes 0.19.0.

Runs the script on a small fixture repository with one due architecture page,
against fake_llm_r8.py (an OpenAI-compatible endpoint that asks for
write_file, patch, terminal and execute_code, uses the three kmctl tools, then
answers with a findings block). Then runs knowledge-audit-issue.sh with a stub
gh. The child environment is built here from scratch: no inherited keys or
tokens, a scratch HOME.

Exits 0 only when:
  - the tools offered to the model, in every request, are exactly
    kmctl_read_file, kmctl_search_files and kmctl_list_files;
  - the requested writes were refused and left the fixture repository
    unchanged (target file intact, git status clean);
  - the finding reached the job summary and the posted issue body;
  - a read and a search of /proc/self/environ were refused without the key.
Also records: the key sent as Bearer and the kmctl tools' results.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path("/home/vscode/kmctl.worktrees/audit-any-provider")
SCRIPT = WORKTREE / "action" / "knowledge-audit.sh"
ISSUE = WORKTREE / "action" / "knowledge-audit-issue.sh"
KMCTL = WORKTREE / ".venv" / "bin" / "kmctl"
HERMES_BIN = HERE / "bin"
KMCTL_TOOLS = ["kmctl_list_files", "kmctl_read_file", "kmctl_search_files"]
KEY = "spike-key-7c1e"


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo, check=True, capture_output=True,
    )


def fixture(root):
    repo = root / "repo"
    (repo / ".okf" / "architecture").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "greet.py").write_text("def greet():\n    return 'Hi'\n")
    (repo / ".okf" / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n\n# Bundle\n\n'
        "- [Architecture](architecture/index.md): the design.\n"
    )
    (repo / ".okf" / "log.md").write_text("# Log\n")
    (repo / ".okf" / "architecture" / "index.md").write_text(
        "# Architecture\n\n- [Overview](overview.md): the parts.\n"
    )
    (repo / ".okf" / "architecture" / "overview.md").write_text(
        '---\ntype: architecture\ntitle: "Overview"\ndescription: "The parts."\n'
        "tags: [architecture]\n---\n\n# Overview\n\n`greet()` in src/greet.py says Hello.\n"
    )
    (repo / "target.txt").write_text("original\n")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "fixture")
    return repo


def main():
    root = Path(tempfile.mkdtemp(prefix="r8-", dir=HERE))
    repo = fixture(root)
    target = repo / "target.txt"
    bin_dir = root / "bin"
    bin_dir.mkdir()
    (bin_dir / "kmctl").symlink_to(KMCTL)
    (bin_dir / "gh").write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> "{root}/gh-calls"\n'
        'for a in "$@"; do case "$a" in --body-file) next=1 ;; *) '
        f'[ -n "$next" ] && cp "$a" "{root}/issue-body" && next= ;; esac; done\n'
        '[ "$1 $2" = "issue list" ] && echo "[]"\n'
        "exit 0\n"
    )
    (bin_dir / "gh").chmod(0o755)
    log, portf = root / "requests.jsonl", root / "port"
    srv = subprocess.Popen([sys.executable, "-I", str(HERE / "fake_llm_r8.py"),
                            str(portf), str(log), str(target)])
    for _ in range(100):
        if portf.exists() and portf.read_text():
            break
        time.sleep(0.05)
    base = f"http://127.0.0.1:{portf.read_text()}/v1"
    home = root / "home"
    home.mkdir()
    runner_temp = root / "runner-temp"
    runner_temp.mkdir()
    summary = root / "summary.md"
    summary.write_text("")
    env = {
        "PATH": f"{bin_dir}:{HERMES_BIN}:/usr/local/bin:/usr/bin:/bin",
        "HOME": str(home),
        "LANG": "C.UTF-8",
        "TERM": "dumb",
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_STEP_SUMMARY": str(summary),
        "RUNNER_TEMP": str(runner_temp),
        "KMCTL_PLUGIN_DIR": str(WORKTREE / "plugin"),
        "KMCTL_AUDIT_PROVIDER": "custom",
        "KMCTL_AUDIT_BASE_URL": base,
        "KMCTL_AUDIT_MODEL": "fake-model",
        "KMCTL_AUDIT_API_KEY_ENV": "SPIKE_KEY",
        "SPIKE_KEY": KEY,
        "KMCTL_AUDIT_TIMEOUT": "5m",
    }
    t0 = time.time()
    audit = subprocess.run(["bash", str(SCRIPT)], cwd=repo, env=env,
                           stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=540)
    secs = round(time.time() - t0, 1)
    issue = subprocess.run(["bash", str(ISSUE)], cwd=repo,
                           env={**env, "GH_TOKEN": "stub-token"},
                           capture_output=True, text=True, timeout=60)
    srv.terminate()

    reqs = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    chats = [r for r in reqs if r["method"] == "POST" and r.get("body", {}).get("tools")]
    offered = [sorted(t["function"]["name"] for t in r["body"]["tools"]) for r in chats]
    results = {}
    if chats:
        msgs = chats[-1]["body"].get("messages", [])
        names = {}
        for m in msgs:
            for tc in m.get("tool_calls") or []:
                names[tc["id"]] = tc["function"]["name"] + " " + tc["function"]["arguments"]
        for m in msgs:
            if m.get("role") == "tool":
                results[names.get(m.get("tool_call_id"), "?")] = str(m.get("content"))[:300]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                            capture_output=True, text=True).stdout
    summary_text = summary.read_text()
    body = (root / "issue-body").read_text() if (root / "issue-body").exists() else ""
    auth = sorted({str(r.get("auth")) for r in reqs if r["method"] == "POST"})

    record = {
        "audit_exit": audit.returncode,
        "audit_secs": secs,
        "audit_stderr_tail": audit.stderr[-1500:],
        "issue_exit": issue.returncode,
        "gh_calls": (root / "gh-calls").read_text() if (root / "gh-calls").exists() else "",
        "chat_requests_with_tools": len(chats),
        "offered_tools_per_request": offered,
        "auth_headers": auth,
        "tool_results": results,
        "target_after": target.read_text(),
        "git_status_porcelain": status,
        "summary": summary_text,
        "issue_body_has_finding": "SPIKE-FINDING" in body,
    }
    print(json.dumps(record, indent=1))

    only_three = bool(offered) and all(o == KMCTL_TOOLS for o in offered)
    writes_refused = all(
        "does not exist" in v for k, v in results.items()
        if k.split(" ")[0] in {"write_file", "patch", "terminal", "execute_code"}
    ) and any(k.startswith("write_file") for k in results)
    unchanged = target.read_text() == "original\n" and status == ""
    reached = audit.returncode == 0 and "SPIKE-FINDING" in summary_text and "SPIKE-FINDING" in body
    environ_refused = all(
        "outside the repository" in v and KEY not in v
        for k, v in results.items() if "/proc/self/environ" in k
    )
    print("only the three kmctl tools offered:", only_three)
    print("requested writes refused:", writes_refused)
    print("fixture repository unchanged:", unchanged)
    print("finding reached the summary and the issue body:", reached)
    print("/proc/self/environ refused, key not returned:", environ_refused)
    print("key sent as Bearer:", auth == [f"Bearer {KEY}"])
    ok = only_three and writes_refused and unchanged and reached and environ_refused
    print("RESULT:", "holds" if ok else "fails")
    shutil.rmtree(root / "home", ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
