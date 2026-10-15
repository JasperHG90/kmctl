"""Set a repository up with docs/ and an OKF bundle, never touching a file that exists."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

OKF_VERSION = "0.2"


@dataclass
class ScaffoldResult:
    """What ``scaffold`` wrote, what it left alone, and what the user must finish by hand.

    Paths are relative to the root. A warning names a kept file that does not
    point at a file ``scaffold`` created, because ``scaffold`` never edits a kept file.
    """

    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _files(now: datetime) -> dict[str, str]:
    at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    by = f"process:kmctl/{version('kmctl')}"
    return {
        "docs/README.md": (
            "# Documentation\n\n"
            "Pages for people who use this project, one folder per Diataxis type\n"
            "(tutorials, how-to, reference, explanation). Each page is listed here.\n"
        ),
        ".okf/index.md": (
            f'---\nokf_version: "{OKF_VERSION}"\n---\n\n'
            "# Knowledge bundle\n\n"
            "For agents and people working on this repository.\n\n"
            "- [Manifesto](manifesto.md): what this project is for, its invariants and values.\n"
        ),
        ".okf/log.md": (
            f"# Log\n\n## {now.date().isoformat()}\n\n"
            "- Created the bundle with `kmctl init`: `manifesto`.\n"
        ),
        ".okf/manifesto.md": (
            "---\n"
            "type: manifesto\n"
            'title: "Manifesto"\n'
            'description: "What this project is for, where its parts live, its invariants and its values."\n'
            "generated:\n"
            f"  by: {by}\n"
            f"  at: {at}\n"
            "tags: [manifesto]\n"
            "---\n\n"
            "# Manifesto\n\n"
            "## What this is for\n\n"
            "## Invariants\n\n"
            "## Values\n"
        ),
    }


def scaffold(root: Path, now: datetime | None = None) -> ScaffoldResult:
    """Write docs/README.md and a starter .okf/ bundle under ``root``.

    Parameters
    ----------
    root : Path
        The repository to set up.
    now : datetime | None
        The time written into the bundle; the current UTC time when omitted.

    Returns
    -------
    ScaffoldResult
        The files created, the files that already existed and were kept, and a
        warning for each kept index or log that does not name a new manifesto.
    """
    result = ScaffoldResult()
    for rel, text in _files(now or datetime.now(UTC)).items():
        path = root / rel
        if path.exists():
            result.skipped.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        result.created.append(rel)
    if ".okf/manifesto.md" in result.created:
        index = root / ".okf" / "index.md"
        if (
            ".okf/index.md" in result.skipped
            and "manifesto.md" not in index.read_text()
        ):
            result.warnings.append(
                "the kept .okf/index.md does not link the new manifesto: add "
                "'- [Manifesto](manifesto.md): <one line>' to it"
            )
        log = root / ".okf" / "log.md"
        if ".okf/log.md" in result.skipped and "`manifesto`" not in log.read_text():
            result.warnings.append(
                "the kept .okf/log.md has no line for the new manifesto: append "
                "a dated line naming `manifesto`"
            )
    return result
