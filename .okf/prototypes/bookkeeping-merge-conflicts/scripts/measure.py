#!/usr/bin/env python3
"""Count the merge conflicts in the bookkeeping files of .okf/, and what two fixes remove.

Two sets of merges are replayed with `git merge-tree`, which merges two commits without
touching the working tree:

1. History: every commit in which a branch merged `main` into itself. The two parents are
   merged again, so the result shows the conflicts the author had to resolve.
2. Open pull requests: every pair of open pull requests. A pair that conflicts means that
   after one is merged, the other has to be updated by hand.

Each merge runs three times:

- `git`: git as it is, which is also what GitHub does;
- `union`: `.okf/log.md` and the `.okf/` index files use git's built-in union merge;
- `union+driver`: also `.okf/summary.md` uses merge_summary.py in this folder.

Run from the repository root, after `git fetch origin`:

    python3 .okf/prototypes/bookkeeping-merge-conflicts/scripts/measure.py

It prints the tables in the README and writes the raw rows to results/results.json, which
git ignores: the rows name the files and pull requests of the repository it ran on.
It also counts the lines in `.okf/log.md` on main by their first word.
The pull request part needs the GitHub CLI; without it, that part is skipped.
"""

from __future__ import annotations

import itertools
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
BOOKKEEPING = (".okf/log.md", ".okf/summary.md")
UNION = (
    ".okf/log.md merge=union\n.okf/index.md merge=union\n.okf/*/index.md merge=union\n"
)
DRIVER = ".okf/summary.md merge=okf-summary\n"
MODES = ("git", "union", "union+driver")
EMPTY_TREE = (
    "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # git's id for a tree with no files
)


def git(*args: str, check: bool = True) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if check and done.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def is_bookkeeping(path: str) -> bool:
    return (
        path in BOOKKEEPING
        or (path.startswith(".okf/") and path.endswith("/index.md"))
        or path == ".okf/index.md"
    )


def conflicts(ours: str, theirs: str, attributes: pathlib.Path | None) -> list[str]:
    """The files that conflict when `theirs` is merged into `ours`."""
    # Read no attributes from the checkout, so the `git` run stays git as it is even
    # when the checked-out .gitattributes already sets the union merge.
    config = [f"--attr-source={EMPTY_TREE}"]
    if attributes is not None:
        config += [
            "-c",
            f"core.attributesFile={attributes}",
            "-c",
            f"merge.okf-summary.driver=python3 {HERE / 'merge_summary.py'} %O %A %B",
        ]
    done = subprocess.run(
        ["git", *config, "merge-tree", "--write-tree", "--name-only", ours, theirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode == 0:
        return []
    lines = done.stdout.split("\n")
    end = lines.index("") if "" in lines else len(lines)
    return sorted(set(lines[1:end]))


def replay(
    pairs: list[tuple[str, str, str]], attribute_files: dict[str, pathlib.Path | None]
) -> list[dict]:
    rows = []
    for label, ours, theirs in pairs:
        rows.append(
            {
                "merge": label,
                **{
                    mode: conflicts(ours, theirs, attribute_files[mode])
                    for mode in MODES
                },
            }
        )
    return rows


def table(title: str, rows: list[dict]) -> None:
    print(f"\n{title}: {len(rows)} merges")
    print("| | git | union | union+driver |")
    print("|---|---|---|---|")
    counts = {
        "Merges with a conflict": lambda files: bool(files),
        "... only in bookkeeping files": lambda files: (
            bool(files) and all(is_bookkeeping(f) for f in files)
        ),
        "... only in `.okf/log.md` and `.okf/summary.md`": lambda files: (
            bool(files) and set(files) <= set(BOOKKEEPING)
        ),
        "... in `.okf/log.md`": lambda files: ".okf/log.md" in files,
        "... in `.okf/summary.md`": lambda files: ".okf/summary.md" in files,
        "... in an `.okf/` index file": lambda files: any(
            f.endswith("index.md") and f.startswith(".okf/") for f in files
        ),
        "... in any other file": lambda files: any(
            not is_bookkeeping(f) for f in files
        ),
    }
    for name, test in counts.items():
        print(
            f"| {name} | "
            + " | ".join(str(sum(1 for r in rows if test(r[m]))) for m in MODES)
            + " |"
        )


def main() -> int:
    main_chain = set(git("rev-list", "--first-parent", "origin/main").split())

    history = []
    for line in git("log", "--all", "--merges", "--format=%H %P").splitlines():
        commit, *parents = line.split()
        if commit in main_chain or len(parents) != 2 or parents[1] not in main_chain:
            continue  # keep only: a branch merged a commit of main into itself
        history.append((commit[:7], parents[0], parents[1]))

    pulls = []
    listed = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "200",
            "--json",
            "number,headRefOid",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if listed.returncode == 0:
        for pull in sorted(json.loads(listed.stdout), key=lambda p: p["number"]):
            known = subprocess.run(
                ["git", "cat-file", "-e", pull["headRefOid"] + "^{commit}"],
                capture_output=True,
                check=False,
            )
            # a head that `git fetch origin` did not bring in is left out
            if known.returncode == 0:
                pulls.append((pull["number"], pull["headRefOid"]))
    else:
        print(
            "gh pr list failed, so the open pull requests are skipped", file=sys.stderr
        )
    pairs = [
        (f"#{a[0]}+#{b[0]}", a[1], b[1]) for a, b in itertools.combinations(pulls, 2)
    ]

    with tempfile.TemporaryDirectory() as tmp:
        union = pathlib.Path(tmp) / "union"
        union.write_text(UNION, encoding="utf-8")
        both = pathlib.Path(tmp) / "both"
        both.write_text(UNION + DRIVER, encoding="utf-8")
        files = {"git": None, "union": union, "union+driver": both}
        history_rows = replay(history, files)
        pair_rows = replay(pairs, files)

    print(
        f"main is at {git('rev-parse', '--short', 'origin/main').strip()}; "
        f"{len(pulls)} open pull requests: {', '.join('#' + str(n) for n, _ in pulls)}"
    )
    table("History, a branch merged main into itself", history_rows)
    table("Open pull requests, every pair", pair_rows)

    kinds: dict[str, int] = {}
    for line in git("show", "origin/main:.okf/log.md").splitlines():
        if line.startswith("- "):
            word = line[2:].split(" ", 1)[0]
            kinds[word] = kinds.get(word, 0) + 1
    total = sum(kinds.values())
    print(f"\nLines in .okf/log.md on main, by first word: {total} lines")
    print("| First word | Lines |")
    print("|---|---|")
    common = {word: count for word, count in kinds.items() if count >= 10}
    for word, count in sorted(common.items(), key=lambda kv: -kv[1]):
        print(f"| {word} | {count} |")
    print(f"| any other word | {total - sum(common.values())} |")

    results = HERE.parent / "results"
    results.mkdir(exist_ok=True)
    (results / "results.json").write_text(
        json.dumps(
            {
                "main": git("rev-parse", "origin/main").strip(),
                "pull_requests": [{"number": n, "head": h} for n, h in pulls],
                "history": history_rows,
                "pairs": pair_rows,
                "log_lines": kinds,
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
