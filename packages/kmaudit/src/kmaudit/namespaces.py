"""Namespaces: one per audited folder, each with its own store file under ``.kmaudit/``.

A namespace is the audited folder's path relative to the repository root,
in POSIX form (``.okf``, ``docs``, ``handbook/guides``). Its store is
``ROOT/.kmaudit/<quoted name>.sqlite``, so two folders never share a
section, claim or check.
"""

import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

STORE_DIR = ".kmaudit"
SUFFIX = ".sqlite"
#: Where the audit kept its one store while it was part of kmctl (ADR 0043).
LEGACY_STORE = Path(".kmctl") / "audit.sqlite"
#: The namespace the legacy store is copied into: it only ever audited ``.okf/``.
LEGACY_NAMESPACE = ".okf"


def name_of(root: Path, folder: Path) -> str:
    """The namespace of ``folder``: its path below ``root``, or ``.`` for the root itself."""
    return folder.resolve().relative_to(root.resolve()).as_posix() or "."


def store_file(root: Path, namespace: str) -> Path:
    """The store file of ``namespace`` in the repository at ``root``."""
    return root / STORE_DIR / f"{quote(namespace, safe='')}{SUFFIX}"


def existing(root: Path) -> dict[str, Path]:
    """Each namespace with a store in the repository at ``root``, mapped to its folder.

    The legacy store counts as the ``.okf`` namespace until it is copied, so a
    path inside ``.okf/`` maps to it from the first run.
    """
    found: dict[str, Path] = {}
    folder = root / STORE_DIR
    if folder.is_dir():
        for path in sorted(folder.glob(f"*{SUFFIX}")):
            name = unquote(path.name.removesuffix(SUFFIX))
            found[name] = (root / name).resolve()
    if LEGACY_NAMESPACE not in found and (root / LEGACY_STORE).is_file():
        found[LEGACY_NAMESPACE] = (root / LEGACY_NAMESPACE).resolve()
    return found


@dataclass(frozen=True)
class Namespace:
    """One namespace as ``kmaudit namespaces`` lists it.

    Attributes
    ----------
    namespace : str
        The audited folder's path below the repository root.
    folder : str
        The audited folder's absolute path.
    sections, claims, checks : int
        How many sections, claims and checks (not reasons) its store holds.
    """

    namespace: str
    folder: str
    sections: int
    claims: int
    checks: int


def repository_root(path: Path) -> Path:
    """Git's top level for ``path``, else the parent of ``path``'s folder, as ``resolve_target`` uses."""
    start = path.resolve() if path.is_dir() else path.resolve().parent
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return start.parent
    return Path(out.strip()).resolve()


def _count(store: Path, sql: str) -> int:
    """One count from the store at ``store``, read-only; 0 when its table is not there yet."""
    db = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    try:
        return int(db.execute(sql).fetchone()[0])
    except sqlite3.OperationalError:
        return 0
    finally:
        db.close()


def listing(path: Path) -> list[Namespace]:
    """Each namespace of the repository holding ``path``, with its counts, sorted by name."""
    root = repository_root(path)
    out: list[Namespace] = []
    for name, folder in existing(root).items():
        store = store_file(root, name)
        if not store.is_file():
            store = root / LEGACY_STORE
        out.append(
            Namespace(
                namespace=name,
                folder=str(folder),
                sections=_count(store, "SELECT count(*) FROM sections"),
                claims=_count(store, "SELECT count(*) FROM claims"),
                checks=_count(
                    store, "SELECT count(*) FROM checks WHERE kind = 'check'"
                ),
            )
        )
    return out
