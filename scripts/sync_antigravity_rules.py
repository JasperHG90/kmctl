"""Write kmctl's Antigravity rules from its Claude Code rules (ADR 0020).

APM 0.33.0 writes an Antigravity rule's ``applyTo`` globs as a YAML list when
there are several, which agy refuses, and agy matches a glob holding a ``/``
against the file's absolute path, so a repository-relative glob never matches
(spike:antigravity-rules/3). Written as one string of ``**/`` globs joined by
escaped commas, ``applyTo`` comes out of APM as the single ``globs:`` string
agy reads (spike:apm-hands-back/1). This script writes those copies into
``apm/antigravity/.apm/instructions/`` from ``apm/claude/.apm/instructions/``,
the one source; ``--check`` exits 1, naming each stale file, when a copy
differs, which a test runs.

Usage: uv run python -m scripts.sync_antigravity_rules [--check]
"""

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
#: The rules as written for Claude Code: the one source.
SOURCE = ROOT / "apm" / "claude" / ".apm" / "instructions"
#: The generated copies for Antigravity.
TARGET = ROOT / "apm" / "antigravity" / ".apm" / "instructions"
#: The prefix agy needs on a glob that holds a ``/``.
ANY_FOLDER = "**/"


def antigravity_rule(text: str, source: str) -> str:
    """The Antigravity copy of one Claude Code rule file: ``applyTo`` rewritten, the body unchanged.

    Raises
    ------
    ValueError
        When the file has no front matter or no ``applyTo`` string.
    """
    end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or end == -1:
        raise ValueError(f"{source} has no front matter")
    meta = yaml.safe_load(text[4:end]) or {}
    apply_to = meta.get("applyTo") if isinstance(meta, dict) else None
    if not isinstance(apply_to, str) or not apply_to.strip():
        raise ValueError(f"{source} has no applyTo string")
    globs = [g.strip() for g in apply_to.split(",") if g.strip()]
    globs = [g if g.startswith(ANY_FOLDER) else ANY_FOLDER + g for g in globs]
    joined = "\\, ".join(globs)
    return f"---\napplyTo: '{joined}'\n---\n{text[end + 5 :]}"


def expected() -> dict[str, str]:
    """Every Antigravity rule file, by name, as this script writes it."""
    return {
        path.name: antigravity_rule(path.read_text(encoding="utf-8"), str(path))
        for path in sorted(SOURCE.glob("*.instructions.md"))
    }


def stale() -> list[str]:
    """The Antigravity rule files that are missing, differ or have no Claude source."""
    want = expected()
    have = {p.name for p in TARGET.glob("*.instructions.md")}
    return sorted(
        name
        for name in want.keys() | have
        if name not in have
        or name not in want
        or (TARGET / name).read_text(encoding="utf-8") != want[name]
    )


def main(argv: list[str] | None = None) -> int:
    """Write the Antigravity rules, or with ``--check`` report the stale ones and exit 1."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Change nothing; exit 1 when a copy is stale.",
    )
    args = parser.parse_args(argv)
    if args.check:
        names = stale()
        for name in names:
            print(f"stale: {TARGET.relative_to(ROOT) / name}", file=sys.stderr)
        return 1 if names else 0
    TARGET.mkdir(parents=True, exist_ok=True)
    want = expected()
    for path in TARGET.glob("*.instructions.md"):
        if path.name not in want:
            path.unlink()
    for name, text in want.items():
        (TARGET / name).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
