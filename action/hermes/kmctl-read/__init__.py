"""kmctl's read-only tools for Hermes Agent, used by the CI audit (ADR 0005, I2).

Hermes loads this folder as a user plugin and calls ``register(ctx)``. It
registers one toolset, ``kmctl_read``, with three tools: read a file, search
files for plain text, and list files. Nothing here writes a file or starts a
program, and every path is resolved (symlinks followed) and refused unless it
lies inside the repository root that ``knowledge-audit.sh`` passes in
``KMCTL_READ_ROOT``. That keeps ``/proc``, the run's HOME (and the API key the
process holds) out of the model's reach. Search matches a substring, never a
regex, so no pattern can backtrack for hours.
"""

import json
import os
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Protocol

TOOLSET = "kmctl_read"
ROOT_ENV = "KMCTL_READ_ROOT"
READ_BYTES = 100_000
READ_LINES = 2000
SEARCH_FILE_BYTES = 2_000_000
MAX_MATCHES = 200
MAX_FILES = 500
LINE_CHARS = 300
SKIP_DIRS = {".git"}


class _Context(Protocol):
    """The part of Hermes' plugin context this plugin uses."""

    def register_tool(
        self, name: str, toolset: str, schema: dict, handler: Callable[..., str]
    ) -> None:
        """Add one tool to a toolset."""


class _Refused(Exception):
    """A request the tools will not serve; its text goes back to the model."""


def _root() -> Path:
    """Return the resolved repository root from ``KMCTL_READ_ROOT``.

    Raises
    ------
    _Refused
        If the variable is unset or does not name a folder.
    """
    raw = os.environ.get(ROOT_ENV, "")
    root = Path(raw).resolve() if raw else None
    if root is None or not root.is_dir():
        raise _Refused(
            f"{ROOT_ENV} does not name the repository folder; no file can be read."
        )
    return root


def _inside(root: Path, path: Path) -> bool:
    """Say whether the resolved ``path`` is ``root`` or lies under it."""
    return path == root or path.is_relative_to(root)


def _resolve(root: Path, raw: object) -> Path:
    """Resolve ``raw`` against ``root``, following symlinks, and refuse it outside ``root``."""
    text = str(raw or ".")
    path = Path(text)
    if not path.is_absolute():
        path = root / path
    try:
        path = path.resolve()
    except (OSError, ValueError, RuntimeError) as err:
        raise _Refused(f"cannot resolve {text!r}: {err}") from err
    if not _inside(root, path):
        raise _Refused(
            f"{text!r} is outside the repository; only files under {root} can be read."
        )
    return path


def _files(root: Path, start: Path) -> Iterator[tuple[str, Path]]:
    """Yield ``(path relative to root, resolved file)`` under ``start``, in a stable order.

    Folder symlinks are not followed, and a file symlink whose target lies
    outside ``root`` is skipped.
    """
    if start.is_file():
        yield os.path.relpath(start, root), start
        return
    for folder, dirs, names in os.walk(start, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            walked = Path(folder) / name
            try:
                real = walked.resolve()
            except (OSError, RuntimeError):
                continue
            if _inside(root, real) and real.is_file():
                yield os.path.relpath(walked, root), real


def _guarded(tool: Callable[[Path, dict], str]) -> Callable[..., str]:
    """Wrap a tool so a refusal or a file error comes back as ``{"error": ...}`` text.

    Hermes 0.19.0 passes a string result to the model and turns a dict into a
    contract error, so the error goes back as JSON text.
    """

    def handler(args: dict, **_: object) -> str:
        """Run the tool on Hermes' arguments."""
        try:
            return tool(_root(), args if isinstance(args, dict) else {})
        except _Refused as err:
            return json.dumps({"error": str(err)})
        except OSError as err:
            return json.dumps({"error": f"could not read: {err.strerror or err}"})

    handler.__doc__ = tool.__doc__
    return handler


def _number(raw: object, default: int, low: int, high: int) -> int:
    """Read an integer argument, falling back to ``default`` and clamping it."""
    try:
        value = int(raw) if raw is not None else default
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


def read_file(root: Path, args: dict) -> str:
    """Return a file's lines as ``N|text``, from ``offset``, up to a line and byte cap.

    The file is read in binary and decoded with replacement, so a binary file
    cannot raise. When the cap cuts the file, the result says so and names the
    offset to read on from. A line longer than the byte cap is split.
    """
    path = _resolve(root, args.get("path"))
    if not path.is_file():
        raise _Refused(f"{args.get('path')!r} is not a file.")
    offset = _number(args.get("offset"), 1, 1, 10**9)
    limit = _number(args.get("limit"), READ_LINES, 1, READ_LINES)
    lines: list[str] = []
    used = number = 0
    cut_at = None
    with path.open("rb") as handle:
        while raw := handle.readline(READ_BYTES):
            number += 1
            if number < offset:
                continue
            if len(lines) == limit or (lines and used + len(raw) > READ_BYTES):
                cut_at = number
                break
            used += len(raw)
            lines.append(
                f"{number}|{raw.decode('utf-8', 'replace').rstrip(chr(10)).rstrip(chr(13))}"
            )
    rel = os.path.relpath(path, root)
    if not lines:
        return f"{rel}: no lines from line {offset} (the file has {number})."
    head = f"{rel}, lines {offset}-{offset + len(lines) - 1}:"
    tail = (
        f"[cut: the file goes on; read again with offset={cut_at} for the rest]"
        if cut_at
        else "[end of file]"
    )
    return "\n".join([head, *lines, tail])


def search_files(root: Path, args: dict) -> str:
    """Return ``path:line: text`` for each line holding ``pattern`` as plain text.

    ``pattern`` is a substring, never a regex or a flag. ``ignore_case``
    matches without regard to case. Files with a NUL byte are skipped as
    binary; each file is searched up to a byte cap, and the result says how
    many were cut and when the match cap stopped the search.
    """
    pattern = str(args.get("pattern") or "")
    if not pattern:
        raise _Refused("give the text to search for in 'pattern'.")
    fold = bool(args.get("ignore_case"))
    needle = pattern.casefold() if fold else pattern
    start = _resolve(root, args.get("path"))
    matches: list[str] = []
    cut_files = 0
    stopped = False
    for rel, real in _files(root, start):
        with real.open("rb") as handle:
            data = handle.read(SEARCH_FILE_BYTES + 1)
        if b"\0" in data[:8192]:
            continue
        if len(data) > SEARCH_FILE_BYTES:
            cut_files += 1
            data = data[:SEARCH_FILE_BYTES]
        # Split on newline only, as kmctl_read_file counts lines, so path:line agrees.
        text = data.decode("utf-8", "replace")
        for number, line in enumerate(text.split("\n"), 1):
            line = line.rstrip("\r")
            if needle in (line.casefold() if fold else line):
                matches.append(f"{rel}:{number}: {line[:LINE_CHARS]}")
                if len(matches) == MAX_MATCHES:
                    stopped = True
                    break
        if stopped:
            break
    notes = []
    if stopped:
        notes.append(
            f"[stopped after {MAX_MATCHES} matches; there may be more. Search a narrower path or longer text.]"
        )
    if cut_files:
        notes.append(
            f"[{cut_files} file(s) larger than {SEARCH_FILE_BYTES} bytes were searched only up to that size.]"
        )
    if not matches:
        return "\n".join([f"no line holds {pattern!r}.", *notes])
    return "\n".join([*matches, *notes])


def list_files(root: Path, args: dict) -> str:
    """Return the files under ``path``, one per line, relative to the repository root.

    With ``contains``, only the files whose relative path holds that text
    (``ignore_case`` to match without regard to case). The result says when
    the file cap stopped the listing.
    """
    start = _resolve(root, args.get("path"))
    contains = str(args.get("contains") or "")
    fold = bool(args.get("ignore_case"))
    needle = contains.casefold() if fold else contains
    found: list[str] = []
    stopped = False
    for rel, _ in _files(root, start):
        if needle in (rel.casefold() if fold else rel):
            if len(found) == MAX_FILES:
                stopped = True
                break
            found.append(rel)
    if stopped:
        found.append(
            f"[stopped after {MAX_FILES} files; there are more. List a narrower path or add 'contains'.]"
        )
    return "\n".join(found) if found else "no file matches."


_PATH = {
    "type": "string",
    "description": "A path relative to the repository root, or an absolute path inside it. Default: the root.",
}
_IGNORE_CASE = {
    "type": "boolean",
    "description": "Match without regard to case. Default: false.",
}

SCHEMAS = {
    "kmctl_read_file": {
        "description": "Read one text file in the repository, as 'LINE|text' lines. Paths outside the repository are refused. Long files are cut; the result then names the offset to read on from.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    **_PATH,
                    "description": "The file: relative to the repository root, or absolute inside it.",
                },
                "offset": {
                    "type": "integer",
                    "description": "The first line to read, from 1. Default: 1.",
                    "minimum": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": f"How many lines to read, at most {READ_LINES}. Default: {READ_LINES}.",
                    "minimum": 1,
                    "maximum": READ_LINES,
                },
            },
            "required": ["path"],
        },
    },
    "kmctl_search_files": {
        "description": "Search the repository's files for lines holding a piece of plain text (not a regex), and return them as 'path:line: text'. Paths outside the repository are refused. The result says when it stopped at its match cap.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The exact text to find. It is never read as a regex or an option.",
                },
                "path": {
                    **_PATH,
                    "description": "A file or folder to search in. Default: the repository root.",
                },
                "ignore_case": _IGNORE_CASE,
            },
            "required": ["pattern"],
        },
    },
    "kmctl_list_files": {
        "description": "List the files under a folder of the repository, optionally only those whose path holds a piece of text (such as '.py' or a file name). Paths outside the repository are refused. The result says when it stopped at its file cap.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    **_PATH,
                    "description": "The folder to list. Default: the repository root.",
                },
                "contains": {
                    "type": "string",
                    "description": "Only files whose path, relative to the root, holds this text.",
                },
                "ignore_case": _IGNORE_CASE,
            },
        },
    },
}

TOOLS = {
    "kmctl_read_file": read_file,
    "kmctl_search_files": search_files,
    "kmctl_list_files": list_files,
}


def register(ctx: _Context) -> None:
    """Register the ``kmctl_read`` toolset with Hermes' plugin context."""
    for name, tool in TOOLS.items():
        ctx.register_tool(
            name=name,
            toolset=TOOLSET,
            schema={"name": name, **SCHEMAS[name]},
            handler=_guarded(tool),
        )
