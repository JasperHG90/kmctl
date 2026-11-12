"""A small git repository with an OKF bundle, for the ``kmctl audit`` tests."""

import json
import subprocess
from pathlib import Path

INDEX = '---\nokf_version: "0.2"\n---\n\n# Bundle\n'

TOOL = """---
type: architecture
title: The tool
description: What the tool does.
---

# The tool

## Parts

The CLI writes `out.txt`. It reads `config.toml` on start.

```python
# not a header
x = 1
```

## Values

Plain words beat jargon.
"""

RECORD = """---
type: decision
title: Use SQLite
status: stable
description: Why SQLite.
---

# Use SQLite

## Decision

The store is SQLite. We first tried Redis.

## Correction, 2026-01-02

The store moved to a folder in the repository.
"""

OLD = """---
type: decision
title: Old
status: deprecated
description: Gone.
---

# Old

The tool used to print XML.
"""

CODE = """import json
import sys

MAX_RETRIES = 3


def main() -> None:
    \"\"\"Write out.txt.\"\"\"
    # retries stop after MAX_RETRIES
    if len(sys.argv) > 2:
        sys.exit(1)
    open("out.txt", "w").write("hi")
"""

WORKFLOW = """jobs:
  audit:
    runs-on: ubuntu-latest
    timeout-minutes: 10
"""

SCRIPT = """import argparse

parser = argparse.ArgumentParser(description="Release the tool.")
parser.add_argument("--fast", action="store_true", help="Skip the slow checks.")
parser.parse_args()
"""


def git(root: Path, *args: str) -> str:
    """Run git in ``root`` and return its stdout."""
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout


def make_repo(root: Path) -> Path:
    """Write the fixture repository at ``root``, commit it, and return ``root``."""
    files = {
        ".okf/index.md": INDEX,
        ".okf/tool.md": TOOL,
        ".okf/decisions/0001-use-sqlite.md": RECORD,
        ".okf/decisions/0002-old.md": OLD,
        ".okf/log.md": "# Log\n",
        ".okf/prototypes/spike/README.md": "---\ntype: prototype\n---\n\n# Spike\n\nIt measured things.\n",
        "src/tool.py": CODE,
        "ci/audit.yml": WORKFLOW,
        "scripts/release.py": SCRIPT,
        "README.md": "The CLI writes out.txt.\n",
        "CHANGELOG.md": "- The CLI writes out.txt.\n",
        "pyproject.toml": '[project]\nname = "tool"\nversion = "0"\n\n[project.scripts]\ntool = "tool.cli:main"\n',
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "init", "-q", "-b", "main")
    git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "add", ".")
    git(
        root,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
        "commit",
        "-qm",
        "init",
    )
    return root


def store_claims(
    root: Path, claims: dict[str, list[tuple[int, str, str]]]
) -> dict[str, str]:
    """Store claims for the fixture's sections as an agent would, and return each claim text's id.

    ``claims`` maps a section id to (sentence number, kind, claim text); every
    other sentence of a named section gets kind none.
    """
    from kmctl.claims.models import claim_id
    from kmctl.claims.sections import cut, resolve_target
    from kmctl.claims.verbs import submit, todo

    todo(root)  # brings the store's sections in line with the bundle
    sections = {s.id: s for s in cut(resolve_target(root))}
    answers = []
    for sid, given in claims.items():
        by_n = {n: (kind, text) for n, kind, text in given}
        verdicts = []
        for n in range(1, len(sections[sid].sentences) + 1):
            kind, text = by_n.get(n, ("none", ""))
            verdicts.append(
                {
                    "n": n,
                    "kind": kind,
                    "claims": [{"claim": text}] if kind != "none" else [],
                }
            )
        answers.append(
            {"section": sid, "key": sections[sid].key, "sentences": verdicts}
        )
    result = submit(root, json.dumps(answers))
    assert not result.refused, result.refused
    return {
        text: claim_id(sid.split("#")[0], text)
        for sid, given in claims.items()
        for _, _, text in given
    }
