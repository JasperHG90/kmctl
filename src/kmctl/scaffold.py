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


def _text(path: Path) -> str | None:
    """The UTF-8 text of ``path``, or None when it is not UTF-8."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


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
        index_text = _text(root / ".okf" / "index.md")
        log_text = _text(root / ".okf" / "log.md")
        for rel, text in ((".okf/index.md", index_text), (".okf/log.md", log_text)):
            if rel in result.skipped and text is None:
                result.warnings.append(
                    f"the kept {rel} is not UTF-8 text, so kmctl cannot tell whether it "
                    "names the new manifesto; check it by hand"
                )
        if (
            ".okf/index.md" in result.skipped
            and index_text is not None
            and "manifesto.md" not in index_text
        ):
            result.warnings.append(
                "the kept .okf/index.md does not link the new manifesto: add "
                "'- [Manifesto](manifesto.md): <one line>' to it"
            )
        if (
            ".okf/log.md" in result.skipped
            and log_text is not None
            and "`manifesto`" not in log_text
        ):
            result.warnings.append(
                "the kept .okf/log.md has no line for the new manifesto: append "
                "a dated line naming `manifesto`"
            )
    return result
